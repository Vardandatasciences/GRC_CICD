<template>
  <div class="document-handling-container">
    <div class="page-header">
      <h1 class="page-title">
        <i class="fas fa-file-alt"></i>
        Document Handling
      </h1>
      <p class="page-subtitle">Manage and view all uploaded documents across modules</p>
    </div>

    <!-- Upload Section -->
    <div class="upload-section">
      <div class="upload-header">
        <h3>
          <i class="fas fa-cloud-upload-alt"></i>
          Upload Document
        </h3>
      </div>
      <div class="upload-form">
        <div class="form-row">
          <div class="form-group">
            <label for="file-input">
              <i class="fas fa-file"></i> Select File
            </label>
            <input 
              type="file" 
              id="file-input"
              ref="fileInput"
              @change="handleFileSelect"
              class="file-input"
              accept=".pdf,.doc,.docx,.xlsx,.xls,.csv,.txt"
            />
            <button @click="triggerFileInput" class="file-select-btn">
              <i class="fas fa-folder-open"></i>
              {{ selectedFile ? selectedFile.name : 'Choose File' }}
            </button>
          </div>

          <div class="form-group">
            <label for="module-select">
              <i class="fas fa-cubes"></i> Module *
            </label>
            <select v-model="uploadModule" id="module-select" class="form-select">
              <option value="">-- Select Module --</option>
              <option value="policy">Policy</option>
              <option value="audit">Audit</option>
              <option value="incident">Incident</option>
              <option value="risk">Risk</option>
            </select>
          </div>

          <div class="form-group">
            <label for="framework-select">
              <i class="fas fa-sitemap"></i> Framework (Optional)
            </label>
            <select v-model="uploadFramework" id="framework-select" class="form-select">
              <option value="">-- No Framework --</option>
              <option
                v-for="fw in frameworks"
                :key="fw.FrameworkId"
                :value="fw.FrameworkName"
              >
                {{ fw.FrameworkName }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <button 
              @click="uploadDocument" 
              :disabled="!selectedFile || !uploadModule || uploading"
              class="upload-btn"
            >
              <i :class="uploading ? 'fas fa-spinner fa-spin' : 'fas fa-cloud-upload-alt'"></i>
              {{ uploading ? 'Uploading...' : 'Upload Document' }}
            </button>
          </div>
        </div>

        <!-- Upload Progress -->
        <div v-if="uploadProgress" class="upload-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
          </div>
          <span class="progress-text">{{ uploadProgress }}%</span>
        </div>

        <!-- Upload Status Message -->
        <div v-if="uploadMessage" :class="['upload-message', uploadMessageType]">
          <i :class="uploadMessageType === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'"></i>
          {{ uploadMessage }}
        </div>
      </div>
    </div>

    <!-- Background Fetch Indicator -->
    <div v-if="isBackgroundFetching" class="background-fetch-indicator">
      <i class="fas fa-sync fa-spin"></i>
      Loading documents in background...
    </div>

    <!-- Module Tabs -->
    <div class="module-tabs">
      <button 
        v-for="module in modules" 
        :key="module.id"
        @click="activeModule = module.id"
        :class="['tab-button', { active: activeModule === module.id }]"
      >
        <i :class="module.icon"></i>
        {{ module.name }}
        <span class="document-count">({{ getDocumentCount(module.id) }})</span>
      </button>
    </div>

    <!-- Document List -->
    <div class="document-list-container">
      <div class="list-header">
        <h2>{{ getActiveModuleName() }}{{ activeModule !== 'all' ? ' Documents' : '' }}</h2>
        <div class="list-actions">
          <div class="search-box">
            <i class="fas fa-search"></i>
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="Search documents..."
              class="search-input"
            />
          </div>
          <div class="filter-dropdown">
            <select v-model="selectedFilter" class="filter-select">
              <option value="all">All Documents</option>
              <option value="pdf">PDF Files</option>
              <option value="doc">DOC Files</option>
              <option value="docx">DOCX Files</option>
              <option value="xlsx">Excel Files</option>
              <option value="csv">CSV Files</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Error State (only show if critical error) -->
      <div v-if="error && !isBackgroundFetching && documents.length === 0" class="error-state">
        <i class="fas fa-exclamation-triangle"></i>
        <h3>Error Loading Documents</h3>
        <p>{{ error }}</p>
        <button @click="loadDocuments" class="btn btn-primary">
          <i class="fas fa-redo"></i> Retry
        </button>
      </div>

      <!-- ALWAYS show the document table - no loading state blocking it -->
      <div class="document-table">
        <div class="table-header">
          <div class="header-cell name-cell">Document Name</div>
          <div class="header-cell time-cell">Upload Time</div>
          <div class="header-cell person-cell">Uploaded By</div>
          <div class="header-cell module-cell">Module</div>
        </div>

        <div class="table-body">
          <div 
            v-for="document in filteredDocuments" 
            :key="document.id"
            class="table-row"
          >
            <div class="table-cell name-cell">
              <div class="document-info" @click="openDocument(document)">
                <i :class="getFileIcon(document.fileType)" class="file-icon"></i>
                <span class="document-name">{{ document.name }}</span>
              </div>
            </div>
            <div class="table-cell time-cell">
              <span class="upload-time">{{ formatDate(document.uploadTime) }}</span>
            </div>
            <div class="table-cell person-cell">
              <div class="user-info">
                <span class="user-name">{{ document.uploadedBy }}</span>
              </div>
            </div>
            <div class="table-cell module-cell">
              <span class="module-badge" :class="document.module.toLowerCase()">
                {{ document.module }}
              </span>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="filteredDocuments.length === 0 && !isBackgroundFetching" class="empty-state">
          <i class="fas fa-file-alt empty-icon"></i>
          <h3>No documents found</h3>
          <p v-if="!searchQuery">{{ error || 'No documents have been uploaded yet. Upload your first document above!' }}</p>
          <p v-else>No documents match your current search criteria.</p>
        </div>
        
        <!-- Loading State (Background) -->
        <div v-if="filteredDocuments.length === 0 && isBackgroundFetching" class="empty-state">
          <i class="fas fa-sync fa-spin empty-icon"></i>
          <h3>Loading documents...</h3>
          <p>Fetching your documents from the server. This won't take long!</p>
        </div>
      </div>
    </div>

    <!-- Document Details Modal -->
    <div v-if="showModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Document Details</h3>
          <button @click="closeModal" class="close-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body" v-if="selectedDocument">
          <div class="detail-row">
            <label>Document Name:</label>
            <span>{{ selectedDocument.name }}</span>
          </div>
          <div class="detail-row">
            <label>File Type:</label>
            <span>{{ selectedDocument.fileType.toUpperCase() }}</span>
          </div>
          <div class="detail-row">
            <label>File Size:</label>
            <span>{{ selectedDocument.fileSize }}</span>
          </div>
          <div class="detail-row">
            <label>Uploaded By:</label>
            <span>{{ selectedDocument.uploadedBy }}</span>
          </div>
          <div class="detail-row">
            <label>Upload Time:</label>
            <span>{{ formatDate(selectedDocument.uploadTime) }}</span>
          </div>
          <div class="detail-row">
            <label>Module:</label>
            <span class="module-badge" :class="selectedDocument.module.toLowerCase()">
              {{ selectedDocument.module }}
            </span>
          </div>
          <div class="detail-row">
            <label>Description:</label>
            <span>{{ selectedDocument.description || 'No description available' }}</span>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="openDocument(selectedDocument)" class="btn btn-primary">
            <i class="fas fa-eye"></i> View Document
          </button>
          <button @click="downloadDocument(selectedDocument)" class="btn btn-secondary">
            <i class="fas fa-download"></i> Download
          </button>
          <button @click="closeModal" class="btn btn-cancel">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { API_ENDPOINTS } from '@/config/api'
import documentDataService from '@/services/documentService'
import './DocumentHandling.css'
import './background-fetch.css'

export default {
  name: 'DocumentHandling',
  setup() {
    const activeModule = ref('all')
    const searchQuery = ref('')
    const selectedFilter = ref('all')
    const showModal = ref(false)
    const selectedDocument = ref(null)
    // NEVER show loading spinner - always load instantly
    const loading = ref(false)
    const error = ref(null)
    const isBackgroundFetching = ref(false)
    
    // Upload form state
    const selectedFile = ref(null)
    const uploadModule = ref('')
    const uploadFramework = ref('')
    const uploading = ref(false)
    const uploadProgress = ref(0)
    const uploadMessage = ref('')
    const uploadMessageType = ref('success')
    const fileInput = ref(null)
    const frameworks = ref([])

    const SYNTHETIC_MODULE = 'synthetic'
    const isSyntheticModule = (moduleName) => (moduleName || '').toLowerCase() === SYNTHETIC_MODULE
    const sanitizeDocuments = (docs = []) => docs.filter(doc => !isSyntheticModule(doc.module))
    const createEmptyCounts = () => ({
      all: 0,
      policy: 0,
      audit: 0,
      incident: 0,
      risk: 0,
      event: 0
    })

    // Module definitions
    const modules = ref([
      { id: 'all', name: 'All Documents', icon: 'fas fa-folder-open' },
      { id: 'policy', name: 'Policy', icon: 'fas fa-file-alt' },
      { id: 'audit', name: 'Audit', icon: 'fas fa-clipboard-check' },
      { id: 'incident', name: 'Incident', icon: 'fas fa-exclamation-circle' },
      { id: 'risk', name: 'Risk', icon: 'fas fa-exclamation-triangle' },
      { id: 'event', name: 'Event', icon: 'fas fa-calendar-alt' }
    ])

    // Document data from service - Load from cache IMMEDIATELY
    const cachedDocuments = sanitizeDocuments(documentDataService.getData('documents') || [])
    const cachedCounts = documentDataService.getData('documentCounts') || createEmptyCounts()
    
    const documents = ref(cachedDocuments)
    const documentCounts = ref(cachedCounts)
    
    // Log cache status - IMMEDIATE
    console.log('[DocumentHandling] ⚡ Component setup START - Loading INSTANTLY')
    console.log('[DocumentHandling] 📊 Cache status:', {
      hasCachedDocs: cachedDocuments.length > 0,
      cachedDocsCount: cachedDocuments.length,
      counts: cachedCounts
    })
    console.log('[DocumentHandling] ✅ Page will display in <50ms - NO BLOCKING!')

    // Load documents - ALWAYS instant, fetch in background if needed
    const loadDocuments = async () => {
      console.log('[DocumentHandling] ⚡ INSTANT LOAD - No waiting!')
      
      // Verify user is authenticated before loading
      const isAuthenticated = localStorage.getItem('is_logged_in') === 'true' && 
                             localStorage.getItem('access_token') !== null
      
      if (!isAuthenticated) {
        console.warn('[DocumentHandling] ⚠️ User not authenticated, cannot load documents')
        error.value = 'Please log in to view documents'
        loading.value = false
        return
      }
      
      // ==========================================
      // NEW: Three-tier fallback pattern
      // ==========================================
      console.log('[DocumentHandling] Checking for cached document data...')
      
      // Tier 1: Check if data is already cached from HomeView prefetch
      if (documentDataService.hasValidCache()) {
        console.log('[DocumentHandling] ✅ Using cached document data from HomeView prefetch')
        const cachedDocs = sanitizeDocuments(documentDataService.getData('documents') || [])
        const cachedCounts = documentDataService.getData('documentCounts') || createEmptyCounts()
        
        // Set data immediately - NO WAITING
        documents.value = cachedDocs
        documentCounts.value = cachedCounts
        loading.value = false
        error.value = null
        
        console.log(`[DocumentHandling] ✅ Displayed ${cachedDocs.length} documents from cache`)
        return
      }
      
      // Tier 2: Check if prefetch is in progress
      if (window.documentDataFetchPromise) {
        console.log('[DocumentHandling] ⏳ Waiting for ongoing prefetch to complete...')
        isBackgroundFetching.value = true
        
        try {
          await window.documentDataFetchPromise
          
          // Update with prefetched data
          documents.value = sanitizeDocuments(documentDataService.getData('documents') || [])
          documentCounts.value = documentDataService.getData('documentCounts') || createEmptyCounts()
          
          console.log(`[DocumentHandling] ✅ Prefetch complete: ${documents.value.length} documents`)
          loading.value = false
          return
          
        } catch (err) {
          console.error('[DocumentHandling] ❌ Prefetch failed:', err)
        } finally {
          isBackgroundFetching.value = false
        }
      }
      
      // Tier 3: Last resort - fetch directly from API
      console.log('[DocumentHandling] 🔄 Fetching document data from API (cache miss)...')
      isBackgroundFetching.value = true
      
      try {
        await documentDataService.fetchAllDocumentData()
        
        // Update with fresh data
        documents.value = sanitizeDocuments(documentDataService.getData('documents') || [])
        documentCounts.value = documentDataService.getData('documentCounts') || createEmptyCounts()
        
        console.log(`[DocumentHandling] ✅ API fetch complete: ${documents.value.length} documents`)
        loading.value = false
        
      } catch (err) {
        console.error('[DocumentHandling] ❌ API fetch failed:', err)
        error.value = 'Failed to load documents. Please refresh.'
        loading.value = false
      } finally {
        isBackgroundFetching.value = false
      }
    }

    // Load all frameworks from backend (show complete list from DB)
    const loadFrameworks = async () => {
      try {
        // Fetch all frameworks (including all statuses) so user can see everything
        const response = await axios.get(API_ENDPOINTS.FRAMEWORKS, {
          params: { include_all_status: true },
          withCredentials: true
        })

        // Backend returns a plain list of frameworks
        const data = Array.isArray(response.data)
          ? response.data
          : (response.data?.data || [])

        frameworks.value = data
        console.log('[DocumentHandling] ✅ Loaded frameworks for upload dropdown:', frameworks.value.length)
      } catch (err) {
        console.error('[DocumentHandling] ❌ Error loading frameworks for upload dropdown:', err)
      }
    }

    // Fetch documents from API (for filtering/searching) - Non-blocking
    const fetchDocuments = async () => {
      try {
        // Don't show loading spinner - keep page interactive
        isBackgroundFetching.value = true
        error.value = null
        
        console.log('[DocumentHandling] 🔍 Filtering/searching documents...')
        
        // Build query parameters
        const params = {
          module: activeModule.value,
          search: searchQuery.value,
          file_type: selectedFilter.value
        }
        
        const response = await axios.get(API_ENDPOINTS.DOCUMENTS_LIST, {
          params,
          withCredentials: true
        })
        
        if (response.data.success) {
          const sanitizedDocs = sanitizeDocuments(response.data.documents)
          documents.value = sanitizedDocs
          // Update cache with filtered results
          documentDataService.setData('documents', sanitizedDocs)
          console.log('✅ Documents filtered:', documents.value.length)
        } else {
          error.value = 'Failed to load documents'
          console.error('❌ Error loading documents:', response.data.error)
        }
      } catch (err) {
        error.value = 'Failed to fetch documents from server'
        console.error('❌ Error fetching documents:', err)
      } finally {
        isBackgroundFetching.value = false
      }
    }

    // Fetch document counts
    const fetchDocumentCounts = async () => {
      try {
        const response = await axios.get(API_ENDPOINTS.DOCUMENTS_COUNTS, {
          withCredentials: true
        })
        
        if (response.data.success) {
          const counts = { ...createEmptyCounts(), ...(response.data.counts || {}) }
          documentCounts.value = counts
          // Update cache
          documentDataService.setData('documentCounts', counts)
        }
      } catch (err) {
        console.error('❌ Error fetching document counts:', err)
      }
    }

    // Track if component is mounted
    const isMounted = ref(false)

    // Watch for changes to trigger re-fetch (skip on initial mount)
    watch([activeModule, searchQuery, selectedFilter], () => {
      if (isMounted.value) {
        console.log('🔍 Filter changed, fetching documents...')
        fetchDocuments()
      }
    })

    // Initial load - ALWAYS instant, no blocking
    onMounted(() => {
      console.log('📄 Document Handling component mounted - INSTANT DISPLAY')
      
      // Check if user is authenticated before loading documents
      const isAuthenticated = localStorage.getItem('is_logged_in') === 'true' && 
                             localStorage.getItem('access_token') !== null
      
      if (!isAuthenticated) {
        console.warn('[DocumentHandling] ⚠️ User not authenticated, skipping document load')
        error.value = 'Please log in to view documents'
        isMounted.value = true
        return
      }
      
      // Load immediately (non-blocking) - only after authentication check
      loadDocuments()

      // Load full framework list for the upload dropdown
      loadFrameworks()
      
      // Mark as mounted
      isMounted.value = true
      
      console.log('[DocumentHandling] 🚀 Component ready - page displayed instantly!')
    })

    // Computed properties
    const filteredDocuments = computed(() => {
      // Documents are already filtered by backend, just return them
      return documents.value
    })

    // Methods
    const getDocumentCount = (moduleId) => {
      return documentCounts.value[moduleId] || 0
    }

    const getActiveModuleName = () => {
      const module = modules.value.find(m => m.id === activeModule.value)
      return module ? module.name : 'All Documents'
    }

    const getFileIcon = (fileType) => {
      const icons = {
        pdf: 'fas fa-file-pdf',
        doc: 'fas fa-file-word',
        docx: 'fas fa-file-word',
        xlsx: 'fas fa-file-excel',
        xls: 'fas fa-file-excel',
        csv: 'fas fa-file-csv',
        txt: 'fas fa-file-alt',
        jpg: 'fas fa-file-image',
        png: 'fas fa-file-image'
      }
      return icons[fileType] || 'fas fa-file'
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    const openDocument = (document) => {
      // Open document in new tab using s3Url
      if (document.s3Url) {
        console.log('📂 Opening document:', document.name, 'from', document.s3Url)
      window.open(document.s3Url, '_blank')
      } else {
        console.error('❌ No S3 URL available for document:', document.name)
        alert('Document URL not available')
      }
    }

    const downloadDocument = (document) => {
      // Download document from S3
      if (document.s3Url) {
        console.log('⬇️ Downloading document:', document.name)
        const link = window.document.createElement('a')
      link.href = document.s3Url
      link.download = document.name
      link.target = '_blank'
        window.document.body.appendChild(link)
      link.click()
        window.document.body.removeChild(link)
      } else {
        console.error('❌ No S3 URL available for download:', document.name)
        alert('Document URL not available for download')
      }
    }

    const showDocumentDetails = (document) => {
      selectedDocument.value = document
      showModal.value = true
    }

    const closeModal = () => {
      showModal.value = false
      selectedDocument.value = null
    }

    // Upload Methods
    const triggerFileInput = () => {
      fileInput.value.click()
    }

    const handleFileSelect = (event) => {
      const file = event.target.files[0]
      if (file) {
        selectedFile.value = file
        uploadMessage.value = ''
        console.log('📄 File selected:', file.name, file.size, file.type)
      }
    }

    const uploadDocument = async () => {
      if (!selectedFile.value || !uploadModule.value) {
        uploadMessage.value = 'Please select a file and module'
        uploadMessageType.value = 'error'
        return
      }

      try {
        uploading.value = true
        uploadProgress.value = 0
        uploadMessage.value = ''

        // Get user info from localStorage
        const userId = localStorage.getItem('user_name') || 'unknown-user'

        // Create FormData
        const formData = new FormData()
        formData.append('file', selectedFile.value)
        formData.append('module', uploadModule.value)
        formData.append('framework', uploadFramework.value || '')
        formData.append('user_id', userId)

        console.log('📤 Uploading document...')
        console.log('   File:', selectedFile.value.name)
        console.log('   Module:', uploadModule.value)
        console.log('   Framework:', uploadFramework.value || 'None')
        console.log('   User:', userId)

        // Use documentService for upload (automatically refreshes cache)
        const response = await documentDataService.uploadDocument(formData, (progress) => {
          uploadProgress.value = progress
        })

        if (response.data.success) {
          uploadMessage.value = `✅ Document uploaded successfully! ${response.data.stored_name || ''}`
          uploadMessageType.value = 'success'
          
          // Reset form
          selectedFile.value = null
          uploadModule.value = ''
          uploadFramework.value = ''
          fileInput.value.value = ''
          uploadProgress.value = 0

          // Refresh documents list from cache (service already updated it)
        documents.value = sanitizeDocuments(documentDataService.getData('documents') || [])
          documentCounts.value = documentDataService.getData('documentCounts')

          setTimeout(() => {
            uploadMessage.value = ''
          }, 3000)

          console.log('✅ Upload successful:', response.data)
        } else {
          uploadMessage.value = `❌ Upload failed: ${response.data.error || 'Unknown error'}`
          uploadMessageType.value = 'error'
          console.error('❌ Upload failed:', response.data)
        }

      } catch (err) {
        uploadMessage.value = `❌ Upload error: ${err.response?.data?.error || err.message}`
        uploadMessageType.value = 'error'
        console.error('❌ Upload error:', err)
      } finally {
        uploading.value = false
      }
    }

    return {
      activeModule,
      searchQuery,
      selectedFilter,
      showModal,
      selectedDocument,
      modules,
      documents,
      filteredDocuments,
      loading,
      error,
      documentCounts,
      getDocumentCount,
      getActiveModuleName,
      getFileIcon,
      formatDate,
      openDocument,
      downloadDocument,
      showDocumentDetails,
      closeModal,
      fetchDocuments,
      fetchDocumentCounts,
      // Upload
      selectedFile,
      uploadModule,
      uploadFramework,
      uploading,
      uploadProgress,
      uploadMessage,
      uploadMessageType,
      fileInput,
      triggerFileInput,
      handleFileSelect,
      uploadDocument,
      isBackgroundFetching,
      frameworks,
      loadFrameworks
    }
  }
}
</script>
