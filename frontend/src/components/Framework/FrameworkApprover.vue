<template>
  <div class="framework_main_container">
    <!-- Page Header -->
    <div class="framework_header">
      <div class="framework_title_section">
        <h1 class="framework_title">Framework Approval</h1>
        <p class="framework_subtitle">Review and manage framework approval requests</p>
      </div>
    </div>
    
    <!-- Filter Section -->
    <div class="framework_filter_section">
      <!-- User Selection for Administrators -->
      <div v-if="isGRCAdministrator" class="framework_filter_block">
        <div class="framework_filter_label">
          <i class="fas fa-users"></i>
          <span>USER SELECTION</span>
        </div>
        <select 
          id="userSelect" 
          v-model="selectedUserId" 
          @change="onUserSelectionChange" 
          class="framework_filter_dropdown"
        >
          <option v-for="user in availableUsers" :key="user.UserId" :value="user.UserId">
            {{ user.UserName }} ({{ user.Role }}) - ID: {{ user.UserId }}
          </option>
        </select>
      </div>
      
      <!-- Framework Filter -->
      <div class="framework_filter_block">
        <div class="framework_filter_label">
          <i class="fas fa-filter"></i>
          <span>FRAMEWORK FILTER</span>
        </div>
        <select 
          id="framework-filter" 
          v-model="selectedFrameworkId" 
          @change="onFrameworkSelectionChange"
          class="framework_filter_dropdown"
        >
          <option value="">All Frameworks</option>
          <option 
            v-for="framework in filteredFrameworks" 
            :key="framework.id" 
            :value="framework.id"
          >
            {{ framework.name }}
          </option>
        </select>
      </div>
    </div>
    
    <!-- Active Filter Warning -->
    <!-- <div v-if="selectedFrameworkId" class="filter-active-warning">
      <i class="fas fa-info-circle"></i>
      <span>
        <strong>Filter Active:</strong> Showing frameworks for 
        <strong>{{ getSelectedFrameworkName() }}</strong>
      </span>
      <button @click="clearFrameworkFilter" class="clear-warning-btn">
        <i class="fas fa-times"></i>
        Clear
      </button>
    </div> -->
        
    <!-- Summary Cards Section -->
    <div class="framework_summary_section">
      <div class="framework_summary_item">
        <div class="framework_summary_icon pending">
          <i class="fas fa-clock"></i>
        </div>
        <div class="framework_summary_content">
          <div class="framework_summary_number">{{ pendingApprovalsCount }}</div>
          <div class="framework_summary_label">Pending Review</div>
        </div>
      </div>
      
      <div class="framework_summary_item clickable" @click="navigateToAllPolicies">
        <div class="framework_summary_icon approved">
          <i class="fas fa-check-circle"></i>
        </div>
        <div class="framework_summary_content">
          <div class="framework_summary_number">{{ approvedApprovalsCount }}</div>
          <div class="framework_summary_label">Approved</div>
        </div>
      </div>
      
      <div class="framework_summary_item clickable" @click="navigateToAllPolicies">
        <div class="framework_summary_icon rejected">
          <i class="fas fa-times-circle"></i>
        </div>
        <div class="framework_summary_content">
          <div class="framework_summary_number">{{ rejectedApprovalsCount }}</div>
          <div class="framework_summary_label">Rejected</div>
        </div>
      </div>
    </div>

    <!-- Task Navigation Tabs -->
    <div v-if="userInitialized && !(isGRCAdministrator && !selectedUserId)" class="framework_task_navigation">
      <button 
        class="framework_nav_tab" 
        :class="{ active: activeTab === 'myTasks' }"
        @click="activeTab = 'myTasks'"
      >
        <i class="fas fa-user"></i>
        My Tasks
        <span class="framework_tab_badge">{{ myTasksCount }}</span>
      </button>
      <button 
        class="framework_nav_tab" 
        :class="{ active: activeTab === 'reviewerTasks' }"
        @click="activeTab = 'reviewerTasks'"
      >
        <i class="fas fa-users"></i>
        Reviewer Tasks
        <span class="framework_tab_badge">{{ reviewerTasksCount }}</span>
      </button>
    </div>
    
    <!-- Show message when GRC Administrator hasn't selected a user -->
    <div v-if="isGRCAdministrator && !selectedUserId && userInitialized" class="framework_no_tasks">
      <div class="framework_no_tasks_icon">
        <i class="fas fa-info-circle"></i>
      </div>
      <h3>Select a User</h3>
      <p>Please select a user from the dropdown above to view their framework tasks and reviewer assignments.</p>
    </div>
    
    <!-- Show framework sections when ready -->
    <template v-else-if="userInitialized">

      <!-- My Tasks Tab -->
      <div v-if="activeTab === 'myTasks'" class="framework_tasks_container">
        <CollapsibleTable
          v-for="section in myTasksSections"
          :key="`mytasks-${section.name}-${currentUserId}-${userInitialized}`"
          :section-config="section"
          :table-headers="tableHeaders"
          :is-expanded="expandedSections[section.name]"
          @toggle="toggleSection(section.name)"
          @task-click="openApprovalDetails"
        />
        
        <!-- Rejected Frameworks (Edit & Resubmit) Section -->
        <CollapsibleTable
          v-if="rejectedFrameworks.length"
          :section-config="{
            name: 'Rejected Frameworks (Edit & Resubmit)',
            statusClass: 'rejected',
            tasks: rejectedFrameworks.map(mapFrameworkToTableRow)
          }"
          :table-headers="tableHeaders"
          :is-expanded="expandedSections['Rejected Frameworks (Edit & Resubmit)']"
          @toggle="toggleSection('Rejected Frameworks (Edit & Resubmit)')"
          @task-click="openApprovalDetails"
          @editTask="(task) => openRejectedItem(task.originalData)"
        />
      </div>

      <!-- Reviewer Tasks Tab -->
      <div v-if="activeTab === 'reviewerTasks'" class="framework_tasks_container">
        <CollapsibleTable
          v-for="section in reviewerTasksSections"
          :key="`reviewertasks-${section.name}-${currentUserId}-${userInitialized}`"
          :section-config="section"
          :table-headers="tableHeaders"
          :is-expanded="expandedSections[section.name]"
          @toggle="toggleSection(section.name)"
          @task-click="openApprovalDetails"
        />
      </div>
    </template>

    <!-- Rejection Modal -->
    <div v-if="showRejectModal" class="reject-modal">
      <div class="reject-modal-content">
        <h4>Rejection Reason</h4>
        <p>Please provide a reason for rejecting this {{ currentRejectionType }}</p>
        <textarea 
          v-model="rejectionComment" 
          class="rejection-comment" 
          placeholder="Enter your comments here..."></textarea>
        <div class="reject-modal-actions">
          <button class="cancel-btn" @click="cancelRejection" :disabled="isSubmittingRejection">Cancel</button>
          <button class="confirm-btn" @click="confirmRejection" :disabled="isSubmittingRejection">
            {{ isSubmittingRejection ? 'Submitting...' : 'Confirm Rejection' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Old Rejected Table (Backup) -->
    <div class="rejected-approvals-section" v-if="false && rejectedFrameworks.length">
      <h3>Rejected Frameworks (Edit & Resubmit)</h3>
      <div class="table-container">
        <table class="frameworks-table">
          <thead>
            <tr>
              <th @click="sortRejected('FrameworkId')">FRAMEWORK ID 
                <i class="fas fa-sort"></i>
              </th>
              <th @click="sortRejected('FrameworkName')">NAME 
                <i class="fas fa-sort"></i>
              </th>
              <th @click="sortRejected('Category')">CATEGORY 
                <i class="fas fa-sort"></i>
              </th>
              <th @click="sortRejected('CreatedByName')">CREATED BY 
                <i class="fas fa-sort"></i>
              </th>
              <th @click="sortRejected('CreatedByDate')">CREATED DATE 
                <i class="fas fa-sort"></i>
              </th>
              <th>STATUS</th>
              <th>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="framework in sortedRejectedFrameworks" :key="framework.FrameworkId">
              <td>
                <a href="#" class="framework-id-link" @click.prevent="openRejectedItem(framework)">
                  {{ getFrameworkId(framework) }}
                </a>
              </td>
              <td>{{ framework.ExtractedData.FrameworkName }}</td>
              <td>{{ framework.ExtractedData.Category || 'No Category' }}</td>
              <td>{{ framework.ExtractedData.CreatedByName }}</td>
              <td>{{ formatDate(framework.ExtractedData.CreatedByDate) }}</td>
              <td>
                <span class="status-badge rejected">Rejected</span>
              </td>
              <td class="actions-cell">
                <button class="view-btn" @click="openApprovalDetails({originalData: framework})">
                  <i class="fas fa-eye"></i> View
          </button>
                <button class="edit-btn" @click="openRejectedItem(framework)">
                  <i class="fas fa-edit"></i> Edit
          </button>
              </td>
            </tr>
          </tbody>
        </table>
        </div>
      </div>

    <!-- Edit Modal for Rejected Framework -->
    <div v-if="showEditModal && editingFramework" class="edit-framework-modal">
      <div class="edit-framework-content">
        <div class="modal-header">
          <h3>Edit & Resubmit Framework: {{ getFrameworkId(editingFramework) }}</h3>
          <button class="close-btn" @click="closeEditModal">&times;</button>
        </div>

        <div class="modal-body">
          <!-- Two column layout -->
          <div class="form-columns">
            <div class="form-column">
              <div class="form-field">
                <label>Framework Name:</label>
                <input v-model="editingFramework.ExtractedData.FrameworkName" />
              </div>
              <div class="form-field">
                <label>Category:</label>
                <input v-model="editingFramework.ExtractedData.Category" />
              </div>
              <div class="form-field">
                <label>Effective Date:</label>
                <input type="date" v-model="editingFramework.ExtractedData.EffectiveDate" />
              </div>
            </div>
            <div class="form-column">
              <div class="form-field">
                <label>Framework Description:</label>
                <textarea v-model="editingFramework.ExtractedData.FrameworkDescription"></textarea>
              </div>
              <div class="form-field">
                <label>Start Date:</label>
                <input type="date" v-model="editingFramework.ExtractedData.StartDate" />
              </div>
              <div class="form-field">
                <label>End Date:</label>
                <input type="date" v-model="editingFramework.ExtractedData.EndDate" />
              </div>
            </div>
          </div>

          <!-- Show rejection reason -->
          <div v-if="editingFramework.rejection_reason" class="form-field full-width">
            <label>Rejection Reason:</label>
            <div class="rejection-reason">{{ editingFramework.rejection_reason }}</div>
          </div>
        </div>
        
        <!-- Edit Policies -->
        <div v-if="editingFramework.ExtractedData.policies" class="edit-policies-section">
          <h4>Edit Policies</h4>
          <div v-for="(policy, policyIndex) in editingFramework.ExtractedData.policies" :key="policyIndex" class="edit-policy-item">
            <h5>{{ policy.PolicyName }}</h5>
            <div class="form-row">
              <div class="form-group">
                <label>Policy Name:</label>
                <input v-model="policy.PolicyName" />
              </div>
              <div class="form-group">
                <label>Description:</label>
                <textarea v-model="policy.PolicyDescription"></textarea>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Objective:</label>
                <textarea v-model="policy.Objective"></textarea>
              </div>
              <div class="form-group">
                <label>Scope:</label>
                <textarea v-model="policy.Scope"></textarea>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Policy Type:</label>
                <select v-model="policy.PolicyType" class="form-control" @change="handlePolicyTypeChange(policy)">
                  <option value="">Select Type</option>
                  <option v-for="type in policyTypeOptions" :key="type" :value="type">{{ type }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>Policy Category:</label>
                <select v-model="policy.PolicyCategory" class="form-control" @change="handlePolicyCategoryChange(policy)">
                  <option value="">Select Category</option>
                  <option v-for="category in filteredPolicyCategories(policy.PolicyType)" :key="category" :value="category">{{ category }}</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Policy Sub Category:</label>
                <select v-model="policy.PolicySubCategory" class="form-control">
                  <option value="">Select Sub Category</option>
                  <option v-for="subCategory in filteredPolicySubCategories(policy.PolicyType, policy.PolicyCategory)" :key="subCategory" :value="subCategory">{{ subCategory }}</option>
                </select>
              </div>
            </div>
        
            <!-- Edit Subpolicies -->
            <div v-if="policy.subpolicies" class="edit-subpolicies-section">
              <h6>Edit Sub-Policies</h6>
              <div v-for="(subpolicy, subIndex) in policy.subpolicies" :key="subIndex" class="edit-subpolicy-item">
                <div class="form-row">
                  <div class="form-group">
                    <label>Sub-Policy Name:</label>
                    <input v-model="subpolicy.SubPolicyName" />
                  </div>
                  <div class="form-group">
                    <label>Description:</label>
                    <textarea v-model="subpolicy.Description"></textarea>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Control:</label>
                    <textarea v-model="subpolicy.Control"></textarea>
                  </div>
                  <div class="form-group">
                    <label>Identifier:</label>
                    <input v-model="subpolicy.Identifier" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Warning message for no changes -->
        <div v-if="!hasFrameworkChanges" class="no-changes-warning">
          <div class="warning-icon">⚠️</div>
          <div class="warning-message">
            <strong>No Changes Detected</strong>
            <p>Please modify the framework before resubmitting for review.</p>
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="cancel-btn" @click="closeEditModal">Cancel</button>
          <button 
            class="resubmit-btn" 
            :class="{ 'disabled': !hasFrameworkChanges }"
            @click="resubmitFramework(editingFramework)"
            :disabled="!hasFrameworkChanges">
            Resubmit for Review
          </button>
        </div>
      </div>
    </div>

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import axios from 'axios'
import { PopupService } from '@/modules/popus/popupService'
import PopupModal from '@/modules/popus/PopupModal.vue'
import CollapsibleTable from '@/components/CollapsibleTable.vue'
import { API_ENDPOINTS } from '../../config/api.js'

export default {
  name: 'FrameworkApprover',
  components: {
    PopupModal,
    CollapsibleTable
  },
  data() {
    return {
      approvals: [],
      showRejectModal: false,
      rejectionComment: '',
      currentRejectionType: 'framework',
      currentRejectionItem: null,
      isSubmittingRejection: false, // Add loading state to prevent double submission
      rejectedFrameworks: [],
      showEditModal: false,
      editingFramework: null,
      originalFrameworkData: null, // Store original data for change detection
      // User management - updated from hardcoded values
      currentUserId: null,
      currentUserName: '',
      selectedUserId: null,
      isGRCAdministrator: false,
      availableUsers: [],
      userInitialized: false,
      isReviewer: false, // Will be determined dynamically based on framework
      
      // Framework functionality
      frameworks: [], // List of frameworks
      selectedFrameworkId: '', // Currently selected framework
      policyCategories: [],
      policyCategoriesMap: {},
      expandedSections: {
        'Under Review': true,
        'Approved': true,
        'Rejected': true,
        'Rejected Frameworks (Edit & Resubmit)': true
      },
      tableHeaders: [
        { key: 'id', label: 'Framework ID', sortable: true, width: '150px' },
        { key: 'name', label: 'Name', sortable: true },
        { key: 'category', label: 'Category', sortable: true },
        { key: 'createdBy', label: 'Created By', sortable: true },
        { key: 'createdDate', label: 'Created Date', sortable: true },
        { key: 'actions', label: 'Actions', width: '120px' }
      ],
      rejectedSortConfig: {
        key: 'CreatedByDate',
        direction: 'desc'
      },
      activeTab: 'myTasks',
      
      // Task arrays (following Policy Approval pattern)
      myTasks: [], // Frameworks created by the user
      reviewerTasks: [] // Frameworks where user is the reviewer
    }
  },
  async mounted() {
    console.log('FrameworkApprover component mounted');
    console.log('Initial data state:', {
      isGRCAdministrator: this.isGRCAdministrator,
      currentUserId: this.currentUserId,
      selectedUserId: this.selectedUserId,
      availableUsers: this.availableUsers
    });
    
    // First fetch frameworks and check for selected framework from session
    await this.fetchFrameworks();
    
    // Then initialize user (which will load frameworks with proper framework filter)
    await this.initializeUser();
    
    // After user is initialized, if framework was loaded from session, reload tasks
    // This ensures data is loaded with the correct framework filter
    if (this.userInitialized && this.selectedFrameworkId) {
      console.log('🔄 Reloading tasks with framework filter from session after initialization:', this.selectedFrameworkId);
      await this.loadUserTasks();
      await this.fetchRejectedFrameworks();
    }
  },
  methods: {
    // Initialize user and check role
    async initializeUser() {
      try {
        console.log('Initializing user and checking role...');
        
        // Get current user role
        const response = await axios.get(API_ENDPOINTS.USER_ROLE);
        console.log('User role API response:', response.data);
        
        if (response.data.success) {
          this.currentUserId = response.data.user_id;
          this.currentUserName = response.data.username || response.data.user_name || '';
          
          // Store username in localStorage for fallback
          if (this.currentUserName) {
            localStorage.setItem('user_name', this.currentUserName);
          }
          
          // Check specifically for "GRC Administrator" role
          const userRole = response.data.role;
          console.log('User role received:', userRole);
          
          // Only GRC Administrator should see the user dropdown
          this.isGRCAdministrator = userRole === 'GRC Administrator';
          
          console.log('Is GRC Administrator:', this.isGRCAdministrator);
          
          if (this.isGRCAdministrator) {
            console.log('User is GRC Administrator, fetching all users for dropdown...');
            // Fetch all users for dropdown
            await this.fetchUsers();
            
            // Set default user to current logged-in administrator
            this.selectedUserId = this.currentUserId;
            console.log('Setting default user for administrator to current user:', this.currentUserName);
            // Load frameworks for the current administrator
            console.log('🔄 DEBUG: Loading frameworks for administrator with framework filter:', this.selectedFrameworkId)
            await this.loadUserTasks();
            await this.fetchRejectedFrameworks();
          } else {
            console.log('User is not GRC Administrator, setting selected user to current user');
            // Set selected user to current user for non-administrators
            this.selectedUserId = this.currentUserId;
            
            // Load frameworks for the current user
            console.log('🔄 DEBUG: Loading frameworks for user with framework filter:', this.selectedFrameworkId)
            await this.loadUserTasks();
            await this.fetchRejectedFrameworks();
          }
          
          this.userInitialized = true;
          this.fetchPolicyTypes();
        } else {
          console.error('User role API did not return success:', response.data);
          // Fallback for development/testing
          console.log('Using fallback user role for testing...');
          this.currentUserId = 2; // Default user ID
          this.isGRCAdministrator = false; // Default to non-administrator
          this.selectedUserId = this.currentUserId;
          this.userInitialized = true;
          
          // Load frameworks for the current user
          console.log('🔄 DEBUG: Loading frameworks for fallback user with framework filter:', this.selectedFrameworkId)
          await this.loadUserTasks();
          await this.fetchRejectedFrameworks();
          this.fetchPolicyTypes();
        }
      } catch (error) {
        console.error('Error initializing user:', error);
        // Fallback for development/testing
        console.log('Using fallback user role due to error...');
        this.currentUserId = 2; // Default user ID
        this.isGRCAdministrator = false; // Default to non-administrator  
        this.selectedUserId = this.currentUserId;
        this.userInitialized = true;
        
        // Load frameworks for the current user
        console.log('🔄 DEBUG: Loading frameworks for error fallback user with framework filter:', this.selectedFrameworkId)
        await this.loadUserTasks();
        await this.fetchRejectedFrameworks();
        this.fetchPolicyTypes();
      }
    },

    // Fetch all users for administrator dropdown
    async fetchUsers() {
      try {
        console.log('Fetching users for dropdown...');
        const response = await axios.get(API_ENDPOINTS.USERS_FOR_DROPDOWN);
        console.log('Users API response:', response.data);
        
        if (Array.isArray(response.data)) {
          this.availableUsers = response.data;
        } else if (response.data && response.data.success && Array.isArray(response.data.data)) {
          this.availableUsers = response.data.data;
        } else {
          this.availableUsers = response.data || [];
        }
        
        console.log('Available users loaded:', this.availableUsers.length, 'users');
        
        // If no users found, show error
        if (this.availableUsers.length === 0) {
          console.error('No users found in database');
          alert('Error: No users found. Please contact administrator.');
        }
      } catch (error) {
        console.error('Error fetching users:', error);
        this.availableUsers = [];
        alert('Error: Could not load users list. Please contact administrator.');
      }
    },

    // Handle user selection change
    async onUserSelectionChange() {
      console.log('User selection changed to:', this.selectedUserId);
      if (this.selectedUserId) {
        // Fetch frameworks for the selected user
        await this.loadUserTasks();
        await this.fetchRejectedFrameworks();
      } else {
        // Clear frameworks if no user selected
        this.myTasks = [];
        this.reviewerTasks = [];
        this.rejectedFrameworks = [];
      }
    },

    // Get selected user name for display
    getSelectedUserName() {
      if (!this.selectedUserId) return '';
      
      // If the selected user is the current administrator, return their name
      if (this.selectedUserId == this.currentUserId) {
        return this.currentUserName;
      }
      
      // Otherwise, find the user in the available users list
      const selectedUser = this.availableUsers.find(u => u.UserId == this.selectedUserId);
      return selectedUser ? selectedUser.UserName : `User ${this.selectedUserId}`;
    },
    
    // Navigate to All Policies page
    navigateToAllPolicies() {
      this.$router.push('/policies-list/all');
    },

    // Framework-related methods
    async fetchFrameworks() {
      try {
        console.log('🔍 DEBUG: Fetching frameworks in FrameworkApprover...')
        const response = await axios.get(API_ENDPOINTS.FRAMEWORKS)
        this.frameworks = response.data.map(fw => ({
          id: fw.FrameworkId,
          name: fw.FrameworkName
        }))
        console.log('✅ DEBUG: Frameworks loaded:', this.frameworks)
        
        // Check for selected framework from session after loading frameworks
        await this.checkSelectedFrameworkFromSession()
      } catch (error) {
        console.error('❌ DEBUG: Error fetching frameworks:', error)
      }
    },

    // Check for selected framework from session and set it as default
    async checkSelectedFrameworkFromSession() {
      try {
        console.log('🔍 DEBUG: Checking for selected framework from session in FrameworkApprover...')
        const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
        console.log('📊 DEBUG: Selected framework response:', response.data)
        
        if (response.data && response.data.success && response.data.frameworkId) {
          const sessionFrameworkId = response.data.frameworkId
          console.log('✅ DEBUG: Found selected framework in session:', sessionFrameworkId)
          
          // Check if this framework exists in our loaded frameworks
          const frameworkExists = this.frameworks.find(f => f.id.toString() === sessionFrameworkId.toString())
          
          if (frameworkExists) {
            this.selectedFrameworkId = sessionFrameworkId.toString()
            console.log('✅ DEBUG: Set selectedFrameworkId from session:', this.selectedFrameworkId)
            console.log('✅ DEBUG: Framework exists in loaded frameworks:', frameworkExists.name)
            
            // Save to session to ensure it's properly set (in case it wasn't saved before)
            try {
              const userId = localStorage.getItem('user_id') || 'default_user'
              await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
                frameworkId: this.selectedFrameworkId,
                userId: userId
              })
            } catch (error) {
              console.error('❌ Error saving framework to session:', error)
            }
            
            // Reload tasks after framework is set from session
            // This ensures data is loaded with the correct framework filter
            if (this.userInitialized) {
              console.log('🔄 Reloading tasks with framework filter from session:', this.selectedFrameworkId)
              await this.loadUserTasks()
              await this.fetchRejectedFrameworks()
            }
          } else {
            console.log('⚠️ DEBUG: Framework from session not found in loaded frameworks')
            console.log('📋 DEBUG: Available frameworks:', this.frameworks.map(f => ({ id: f.id, name: f.name })))
            this.selectedFrameworkId = ''
          }
        } else {
          console.log('ℹ️ DEBUG: No framework found in session - showing All Frameworks')
          this.selectedFrameworkId = ''
        }
      } catch (error) {
        console.error('❌ DEBUG: Error checking selected framework from session:', error)
        this.selectedFrameworkId = ''
      }
    },

    // Handle framework selection change
    async onFrameworkSelectionChange() {
      console.log('🔄 Framework changed to:', this.selectedFrameworkId)

      // Save the selected framework to session or clear it
      if (this.selectedFrameworkId && this.selectedFrameworkId !== '') {
        try {
          const userId = localStorage.getItem('user_id') || 'default_user'
          console.log('🔍 DEBUG: Saving framework to session in FrameworkApprover:', this.selectedFrameworkId)
          
          const response = await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
            frameworkId: this.selectedFrameworkId,
            userId: userId
          })
          
          if (response.data && response.data.success) {
            console.log('✅ DEBUG: Framework saved to session successfully in FrameworkApprover')
            console.log('🔑 DEBUG: Session key:', response.data.sessionKey)
          } else {
            console.error('❌ DEBUG: Failed to save framework to session in FrameworkApprover')
          }
        } catch (error) {
          console.error('❌ DEBUG: Error saving framework to session in FrameworkApprover:', error)
        }
      } else {
        // Clear session if no framework selected (All Frameworks)
        console.log('🧹 Clearing framework from session (All Frameworks selected)')
        try {
          const userId = localStorage.getItem('user_id') || 'default_user'
          await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
            frameworkId: null,
            userId: userId
          })
          console.log('✅ Framework cleared from session successfully')
        } catch (error) {
          console.error('❌ Error clearing framework from session:', error)
        }
      }
      
      // Refresh data with the selected framework
      console.log('🔄 DEBUG: Refreshing data with framework filter')
      console.log('🔄 DEBUG: userInitialized:', this.userInitialized)
      if (this.userInitialized) {
        await this.refreshData()
      } else {
        console.log('⚠️ DEBUG: User not initialized yet, skipping data refresh')
      }
    },

    // Get selected framework name for display
    getSelectedFrameworkName() {
      if (!this.selectedFrameworkId) return '';
      
      const selectedFramework = this.frameworks.find(f => f.id.toString() === this.selectedFrameworkId.toString());
      return selectedFramework ? selectedFramework.name : `Framework ${this.selectedFrameworkId}`;
    },

    // Clear framework filter
    clearFrameworkFilter() {
      this.selectedFrameworkId = '';
      this.onFrameworkSelectionChange();
    },

    // Load user tasks (following Policy Approval pattern)
    async loadUserTasks() {
      const targetUserId = this.selectedUserId || this.currentUserId;
      console.log('Loading user tasks for user:', targetUserId);
      console.log('Is GRC Administrator:', this.isGRCAdministrator);
      
      // If administrator and no user selected, don't load any tasks
      if (this.isGRCAdministrator && !this.selectedUserId) {
        console.log('Administrator with no user selected - clearing tasks');
        this.myTasks = [];
        this.reviewerTasks = [];
        return;
      }
      
      try {
        // Fetch My Tasks (where user is the creator/owner)
        await this.fetchMyTasks(targetUserId);
        
        // Fetch Reviewer Tasks (where user is the reviewer)
        await this.fetchReviewerTasks(targetUserId);
      } catch (error) {
        console.error('Error loading user tasks:', error);
        this.myTasks = [];
        this.reviewerTasks = [];
      }
    },

    // Fetch My Tasks (created by user)
    async fetchMyTasks(userId) {
      try {
        console.log('🔍 DEBUG: fetchMyTasks called with userId:', userId);
        
        // Prepare params with framework filter if selected
        const params = {};
        if (this.selectedFrameworkId && this.selectedFrameworkId !== '') {
          params.framework_id = this.selectedFrameworkId;
          console.log('🔍 Adding framework filter to framework my tasks:', this.selectedFrameworkId);
        } else {
          console.log('ℹ️ No framework filter - fetching all frameworks data');
        }
        
        // Fetch framework approvals where user is the creator
        const response = await axios.get(API_ENDPOINTS.FRAMEWORK_APPROVALS_USER(userId), { params });
        
        let approvalsData;
        if (response.data.success && response.data.data) {
          approvalsData = response.data.data;
        } else if (Array.isArray(response.data)) {
          approvalsData = response.data;
        } else {
          approvalsData = [];
        }
        
        console.log('🔍 DEBUG: My Tasks API Response:', {
          userId,
          responseData: response.data,
          approvalsDataLength: approvalsData.length,
          firstFewApprovals: approvalsData.slice(0, 3),
          url: API_ENDPOINTS.FRAMEWORK_APPROVALS_USER(userId)
        });

        this.myTasks = approvalsData.map(approval => {
          return {
            ApprovalId: approval.ApprovalId,
            FrameworkId: approval.FrameworkId,
            ExtractedData: {
              type: 'framework',
              FrameworkName: approval.FrameworkName,
              CreatedByName: approval.CreatedByName,
              CreatedByDate: approval.CreatedByDate,
              CreatedBy: approval.UserId,
              Category: approval.Category,
              Status: approval.FrameworkStatus,
              Reviewer: approval.ReviewerId,
              ReviewerName: approval.ReviewerName,
              ...approval.ExtractedData
            },
            ApprovedNot: approval.ApprovedNot,
            Version: approval.Version,
            version: approval.Version,
            UserId: approval.UserId,
            ReviewerId: approval.ReviewerId
          };
        });

        console.log('✅ My Tasks loaded:', this.myTasks.length);
      } catch (error) {
        console.error('Error fetching my tasks:', error);
        this.myTasks = [];
      }
    },

    // Fetch Reviewer Tasks (where user is reviewer)
    async fetchReviewerTasks(userId) {
      try {
        console.log('🔍 DEBUG: fetchReviewerTasks called with userId:', userId);
        
        // Prepare params with framework filter if selected
        const params = {};
        if (this.selectedFrameworkId && this.selectedFrameworkId !== '') {
          params.framework_id = this.selectedFrameworkId;
          console.log('🔍 Adding framework filter to framework reviewer tasks:', this.selectedFrameworkId);
        } else {
          console.log('ℹ️ No framework filter - fetching all frameworks data');
        }
        
        // Fetch framework approvals where user is the reviewer
        const response = await axios.get(API_ENDPOINTS.FRAMEWORK_APPROVALS_REVIEWER(userId), { params });
        
        let approvalsData;
        if (response.data.success && response.data.data) {
          approvalsData = response.data.data;
        } else if (Array.isArray(response.data)) {
          approvalsData = response.data;
        } else {
          approvalsData = [];
        }
        
        console.log('🔍 DEBUG: Reviewer Tasks API Response:', {
          userId,
          responseData: response.data,
          approvalsDataLength: approvalsData.length,
          firstFewApprovals: approvalsData.slice(0, 3),
          url: API_ENDPOINTS.FRAMEWORK_APPROVALS_REVIEWER(userId)
        });

        this.reviewerTasks = approvalsData.map(approval => {
          return {
            ApprovalId: approval.ApprovalId,
            FrameworkId: approval.FrameworkId,
            ExtractedData: {
              type: 'framework',
              FrameworkName: approval.FrameworkName,
              CreatedByName: approval.CreatedByName,
              CreatedByDate: approval.CreatedByDate,
              CreatedBy: approval.UserId,
              Category: approval.Category,
              Status: approval.FrameworkStatus,
              Reviewer: approval.ReviewerId,
              ReviewerName: approval.ReviewerName,
              ...approval.ExtractedData
            },
            ApprovedNot: approval.ApprovedNot,
            Version: approval.Version,
            version: approval.Version,
            UserId: approval.UserId,
            ReviewerId: approval.ReviewerId
          };
        });

        console.log('✅ Reviewer Tasks loaded:', this.reviewerTasks.length);
      } catch (error) {
        console.error('Error fetching reviewer tasks:', error);
        this.reviewerTasks = [];
      }
    },
    
    // Check if current user is the reviewer for this framework
    isCurrentUserReviewer(framework) {
      if (!framework) {
        console.log('⚠️ No framework provided to isCurrentUserReviewer');
        return false;
      }
      
      if (!this.currentUserId) {
        console.log('⚠️ No currentUserId set in isCurrentUserReviewer');
        console.log('⚠️ userInitialized:', this.userInitialized);
        return false;
      }
      
      console.log('✅ Checking if current user is reviewer for framework:', {
        frameworkId: framework.FrameworkId,
        currentUserId: this.currentUserId,
        currentUserName: this.currentUserName,
        reviewer: framework.ExtractedData?.Reviewer,
        reviewerId: framework.ReviewerId,
        isGRCAdmin: this.isGRCAdministrator,
        userInitialized: this.userInitialized
      });
      
      // For GRC Administrators, they can only review frameworks specifically assigned to them
      if (this.isGRCAdministrator) {
        // Check if they are specifically assigned as the reviewer for this framework
        const reviewerId = framework.ReviewerId || framework.ExtractedData?.Reviewer;
        if (reviewerId && String(reviewerId) === String(this.currentUserId)) {
          console.log('GRC Administrator is specifically assigned as reviewer for this framework');
          return true;
        }
        console.log('GRC Administrator is not assigned as reviewer for this framework');
        return false;
      }
      
      // Check if current user is the reviewer for this framework
      // The reviewer information is stored in the ReviewerId field of the approval record
      const reviewerId = framework.ReviewerId || framework.ExtractedData?.Reviewer;
      
      console.log('Reviewer check details:', {
        reviewerId: reviewerId,
        currentUserId: this.currentUserId,
        frameworkReviewerId: framework.ReviewerId,
        extractedDataReviewer: framework.ExtractedData?.Reviewer
      });
      
      // Check by ID
      if (reviewerId && String(reviewerId) === String(this.currentUserId)) {
        console.log('Current user is the assigned reviewer');
        return true;
      }
      
      // Check if the framework was created by the current user (they shouldn't review their own frameworks)
      if (this.isCurrentUserCreator(framework)) {
        console.log('Current user is the creator - not the reviewer');
        return false;
      }
      
      console.log('Current user is not the reviewer');
      return false;
    },

    // Check if current user can perform review actions (approve/reject)
    canPerformReviewActions(framework) {
      if (!framework || !this.currentUserId) return false;
      
      // Only allow review actions if the user is specifically assigned as the reviewer
      // AND is not the creator of the framework
      return this.isCurrentUserReviewer(framework) && !this.isCurrentUserCreator(framework);
    },

    // Check if current user is the creator of this framework
    isCurrentUserCreator(framework) {
      if (!framework || !this.currentUserId) return false;
      
      const createdBy = framework.ExtractedData?.CreatedByName || framework.CreatedByName;
      const createdById = framework.ExtractedData?.CreatedBy || framework.CreatedBy;
      const userId = framework.ExtractedData?.UserID || framework.UserID;
      
      console.log('Creator check details:', {
        createdBy: createdBy,
        createdById: createdById,
        userId: userId,
        currentUserId: this.currentUserId,
        currentUserName: this.getCurrentUserName(),
        frameworkData: framework.ExtractedData
      });
      
      // Check by ID first (most reliable)
      if (createdById && String(createdById) === String(this.currentUserId)) {
        console.log('Current user is creator (by ID)');
        return true;
      }
      
      // Check by UserID (from approval record)
      if (userId && String(userId) === String(this.currentUserId)) {
        console.log('Current user is creator (by UserID)');
        return true;
      }
      
      // Check by name (fallback)
      if (createdBy && String(createdBy) === String(this.getCurrentUserName())) {
        console.log('Current user is creator (by name)');
        return true;
      }
      

      
      console.log('Current user is not the creator');
      return false;
    },

    // Fetch framework policies and subpolicies
    fetchFrameworkPolicies(frameworkId) {
              axios.get(API_ENDPOINTS.FRAMEWORK_GET_POLICIES(frameworkId))
        .then(response => {
          console.log('Framework policies:', response.data);
          if (response.data) {
            // Update policies with status
            const policies = response.data.map(policy => ({
              ...policy,
              Status: policy.Status || 'Under Review',
              subpolicies: []
            }));

            // Update the framework data with policies
            this.selectedApproval.ExtractedData.policies = policies;

            // For each policy, fetch its subpolicies
            const subpolicyPromises = policies.map(policy => 
              axios.get(API_ENDPOINTS.POLICY_GET_SUBPOLICIES(policy.PolicyId))
                .then(subResponse => {
                  console.log(`Subpolicies for policy ${policy.PolicyId}:`, subResponse.data);
                  if (subResponse.data) {
                    // Find the policy and update its subpolicies
                    const policyToUpdate = this.selectedApproval.ExtractedData.policies.find(p => p.PolicyId === policy.PolicyId);
                    if (policyToUpdate) {
                      policyToUpdate.subpolicies = subResponse.data.map(sub => ({
                        ...sub,
                        Status: sub.Status || 'Under Review'
                      }));
                      console.log(`Updated policy ${policy.PolicyId} with ${subResponse.data.length} subpolicies`);
                    }
                  }
                })
                .catch(error => {
                  console.error(`Error fetching subpolicies for policy ${policy.PolicyId}:`, error);
                })
            );

            // Wait for all subpolicy requests to complete
            Promise.all(subpolicyPromises)
              .then(() => {
                console.log('All policies and subpolicies loaded');
              })
              .catch(error => {
                console.error('Error loading some subpolicies:', error);
              });
          }
        })
        .catch(error => {
          console.error('Error fetching policies:', error);
          PopupService.error('Error loading policies. Please try again.', 'Loading Error');
        });
    },

    openApprovalDetails(task) {
      const framework = task.originalData; // Get the original framework data
      if (!framework) return;

      // Debug logging for user roles
      console.log('Opening framework details:', {
        frameworkId: framework.FrameworkId,
        currentUserId: this.currentUserId,
        isReviewer: this.isCurrentUserReviewer(framework),
        canPerformActions: this.canPerformReviewActions(framework),
        isCreator: this.isCurrentUserCreator(framework),
        isGRCAdmin: this.isGRCAdministrator,
        reviewer: framework.ExtractedData?.Reviewer,
        createdBy: framework.ExtractedData?.CreatedByName,
        approvedNot: framework.ApprovedNot,
        status: framework.ExtractedData?.Status
      });

      // Get the framework ID
      const frameworkId = this.getFrameworkId(framework);

      // Store the framework data in sessionStorage to preserve the correct status
      sessionStorage.setItem('frameworkData', JSON.stringify(framework));

      // Navigate to framework details page instead of showing modal
      this.$router.push({
        name: 'FrameworkDetails',
        params: { frameworkId: frameworkId }
      });
    },
    
    async refreshData() {
      await this.loadUserTasks();
      await this.fetchRejectedFrameworks();
    },
    
    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return ''; // Invalid date
      
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    },
    
    isNewFramework(framework) {
      const createdDate = framework.ExtractedData?.CreatedByDate || framework.created_at;
      if (!createdDate) return false;
      
      const date = new Date(createdDate);
      if (isNaN(date.getTime())) return false; // Invalid date
      
      const threeDaysAgo = new Date();
      threeDaysAgo.setDate(threeDaysAgo.getDate() - 3); // Show new badge for 3 days
      
      return date > threeDaysAgo;
    },
    
    getFrameworkId(framework) {
      if (framework.FrameworkId) {
        return typeof framework.FrameworkId === 'object' ? framework.FrameworkId.FrameworkId : framework.FrameworkId;
      }
      return framework.ApprovalId;
    },
    
    
    approveFramework() {
      if (!this.selectedApproval || !this.selectedApproval.FrameworkId) {
        console.error('No framework selected for approval');
          return;
        }

      // Initialize framework approval if doesn't exist
      if (!this.selectedApproval.ExtractedData.framework_approval) {
        this.selectedApproval.ExtractedData.framework_approval = {};
      }
      this.selectedApproval.ExtractedData.framework_approval.approved = true;
      this.selectedApproval.ExtractedData.framework_approval.remarks = '';
      
      // Update the overall approval status
      this.selectedApproval.ApprovedNot = true;
      this.selectedApproval.ExtractedData.Status = 'Approved';
    },
    
    rejectFramework() {
      this.currentRejectionType = 'framework';
      this.currentRejectionItem = null;
      this.showRejectModal = true;
    },
    
    cancelRejection() {
      this.showRejectModal = false;
      this.rejectionComment = '';
      this.currentRejectionType = 'framework';
      this.currentRejectionItem = null;
      this.isSubmittingRejection = false; // Reset loading state
    },
    
    confirmRejection() {
      if (!this.rejectionComment.trim()) {
        PopupService.warning('Please provide a rejection reason', 'Missing Reason');
        return;
      }

      // Prevent double submission
      if (this.isSubmittingRejection) {
        console.log('Rejection already in progress, preventing duplicate submission');
        return;
      }

      console.log('DEBUG: confirmRejection called');
      console.log('DEBUG: currentRejectionType:', this.currentRejectionType);
      console.log('DEBUG: currentRejectionItem:', this.currentRejectionItem);
      console.log('DEBUG: selectedApproval:', this.selectedApproval);

      this.isSubmittingRejection = true;
      const frameworkId = this.getFrameworkId(this.selectedApproval);
      console.log('DEBUG: frameworkId:', frameworkId);
      
      if (this.currentRejectionType === 'subpolicy' && this.currentRejectionItem) {
        const { policy, subpolicy } = this.currentRejectionItem;
        console.log('DEBUG: Rejecting subpolicy - policy:', policy);
        console.log('DEBUG: Rejecting subpolicy - subpolicy:', subpolicy);
        console.log('DEBUG: rejection_reason:', this.rejectionComment);
        
        const url = API_ENDPOINTS.FRAMEWORK_POLICY_SUBPOLICY_APPROVE_REJECT(frameworkId, policy.PolicyId, subpolicy.SubPolicyId);
        console.log('DEBUG: Calling URL:', url);
        
        // Call backend endpoint for subpolicy rejection
        axios.put(url, {
            approved: false,
          rejection_reason: this.rejectionComment,
          submit_review: true // Add flag to submit review automatically
        })
          .then(response => {
            console.log('Subpolicy rejected successfully:', response.data);

          // Update local state
            subpolicy.Status = 'Rejected';
            policy.Status = 'Rejected';
            if (policy.subpolicies) {
              policy.subpolicies.forEach(sp => {
                sp.Status = 'Rejected';
              });
            }
            this.selectedApproval.ExtractedData.Status = 'Rejected';
            this.selectedApproval.ApprovedNot = false;
            
            // Update the approval record with the response data if available
            if (response.data.ApprovalId) {
              this.selectedApproval.ApprovalId = response.data.ApprovalId;
            }
            if (response.data.Version) {
              this.selectedApproval.Version = response.data.Version;
            }
            
            PopupService.success('Subpolicy rejected. Framework has been rejected and sent back for revision.', 'Subpolicy Rejected');
            this.cancelRejection();
            this.fetchFrameworks();
            this.fetchRejectedFrameworks();
          })
          .catch(error => {
            console.log('DEBUG: Error rejecting subpolicy:', error);
            console.log('DEBUG: Error response:', error.response);
            this.handleError(error, 'rejecting subpolicy');
          })
          .finally(() => {
            this.isSubmittingRejection = false;
          });
          
      } else if (this.currentRejectionType === 'policy' && this.currentRejectionItem) {
        const policy = this.currentRejectionItem;
        console.log('DEBUG: Rejecting policy - policy:', policy);
        console.log('DEBUG: rejection_reason:', this.rejectionComment);
        
        const url = API_ENDPOINTS.FRAMEWORK_POLICY_APPROVE_REJECT(frameworkId, policy.PolicyId);
        console.log('DEBUG: Calling URL:', url);
        
        // Call backend endpoint for policy rejection
        axios.put(url, {
          approved: false,
          rejection_reason: this.rejectionComment,
          submit_review: true // Add flag to submit review automatically
        })
          .then(response => {
            console.log('Policy rejected successfully:', response.data);

          // Update local state
            policy.Status = 'Rejected';
            if (policy.subpolicies) {
              policy.subpolicies.forEach(subpolicy => {
                subpolicy.Status = 'Rejected';
              });
            }
            this.selectedApproval.ExtractedData.Status = 'Rejected';
            this.selectedApproval.ApprovedNot = false;
            
            // Update the approval record with the response data if available
            if (response.data.ApprovalId) {
              this.selectedApproval.ApprovalId = response.data.ApprovalId;
            }
            if (response.data.Version) {
              this.selectedApproval.Version = response.data.Version;
            }
            
            PopupService.success('Policy rejected. Framework has been rejected and sent back for revision.', 'Policy Rejected');
            this.cancelRejection();
            this.fetchFrameworks();
            this.fetchRejectedFrameworks();
          })
          .catch(error => {
            console.log('DEBUG: Error rejecting policy:', error);
            console.log('DEBUG: Error response:', error.response);
            this.handleError(error, 'rejecting policy');
          })
          .finally(() => {
            this.isSubmittingRejection = false;
          });
          
      } else if (this.currentRejectionType === 'framework') {
        // For direct framework rejection, use submitFrameworkReview with rejection reason
        if (!this.selectedApproval || !this.selectedApproval.FrameworkId) {
          console.error('No framework selected for rejection');
          this.cancelRejection();
            return;
          }
        
        // Initialize framework approval if doesn't exist
        if (!this.selectedApproval.ExtractedData.framework_approval) {
          this.selectedApproval.ExtractedData.framework_approval = {};
        }
        
        // Update the framework status and approval state in the UI
        this.selectedApproval.ExtractedData.framework_approval.approved = false;
        this.selectedApproval.ExtractedData.framework_approval.remarks = this.rejectionComment;
        this.selectedApproval.ExtractedData.Status = 'Rejected';
        this.selectedApproval.ApprovedNot = false;
        
        // Submit the review with rejection data
        this.submitFrameworkReview(false, this.rejectionComment);
        
        this.cancelRejection();
        this.isSubmittingRejection = false;
      }
    },
    
    // Helper method to handle and display errors
    handleError(error, context) {
      console.error(`Error ${context}:`, error);
      let errorMessage = 'An unexpected error occurred';
      
      if (error.response) {
        // The server responded with a status code outside of 2xx range
        if (error.response.data && error.response.data.error) {
          errorMessage = error.response.data.error;
        } else if (error.response.data && typeof error.response.data === 'string') {
          errorMessage = error.response.data;
        } else {
          errorMessage = `Server error: ${error.response.status}`;
        }
      } else if (error.request) {
        // The request was made but no response was received
        errorMessage = 'No response from server. Please check your connection.';
      } else {
        // Something happened in setting up the request
        errorMessage = error.message || errorMessage;
      }
      
      PopupService.error(`Error ${context}: ${errorMessage}`, 'Error');
      return errorMessage;
    },
    
    // Helper method to submit framework review
    submitFrameworkReview(approved, remarks = '') {
      if (!this.selectedApproval || !this.selectedApproval.FrameworkId) {
        console.error('No framework selected for review submission');
        return;
      }
      
      // Prevent duplicate submission if framework is already processed
      if (this.selectedApproval.ExtractedData?.Status === 'Rejected') {
        console.log('Framework is already rejected, preventing duplicate submission');
        PopupService.warning('Framework has already been rejected and cannot be submitted again.', 'Already Rejected');
        return;
      }
      
      if (this.selectedApproval.ExtractedData?.Status === 'Approved') {
        console.log('Framework is already approved, preventing duplicate submission');
        PopupService.warning('Framework has already been approved and cannot be submitted again.', 'Already Approved');
        return;
      }
      
      const frameworkId = this.getFrameworkId(this.selectedApproval);
      console.log(`Submitting framework review for framework ${frameworkId}`, {
        approved: approved,
        remarks: remarks
      });
      
      // Preserve the original UserId (framework creator) and set ReviewerId to current user
      const originalUserId = this.selectedApproval.UserId || this.selectedApproval.UserID || this.selectedApproval.ExtractedData?.CreatedBy;
      
      console.log('User ID preservation:', {
        originalUserId: originalUserId,
        currentUserId: this.currentUserId,
        selectedApprovalUserId: this.selectedApproval.UserId,
        selectedApprovalUserID: this.selectedApproval.UserID,
        extractedDataCreatedBy: this.selectedApproval.ExtractedData?.CreatedBy
      });
      
      // Create the framework review data
      const reviewData = {
        ExtractedData: JSON.parse(JSON.stringify(this.selectedApproval.ExtractedData)),
        ApprovedNot: approved,
        remarks: remarks,
        UserId: originalUserId, // Preserve original framework creator's ID
        ReviewerId: this.currentUserId, // Set reviewer ID to current user
        currentVersion: this.selectedApproval.version || this.selectedApproval.Version || 'u1'
      };
      
      // If approving, set all policies and subpolicies to Approved status
      if (approved === true && reviewData.ExtractedData.policies) {
        reviewData.ExtractedData.policies.forEach(policy => {
          policy.Status = 'Approved';
          policy.ActiveInactive = 'Active'; // Set policies to Active when framework is approved
          
              if (policy.subpolicies) {
            policy.subpolicies.forEach(subpolicy => {
              subpolicy.Status = 'Approved';
            });
              }
            });
          }

      // Set framework ActiveInactive to Active when approved
      if (approved === true) {
        reviewData.ExtractedData.ActiveInactive = 'Active';
      }
      
      // If rejecting, ensure framework_approval contains rejection remarks
      if (approved === false && remarks) {
        if (!reviewData.ExtractedData.framework_approval) {
          reviewData.ExtractedData.framework_approval = {};
        }
        reviewData.ExtractedData.framework_approval.remarks = remarks;
      }
      
      // Submit framework review
      axios.post(API_ENDPOINTS.FRAMEWORK_SUBMIT_REVIEW(frameworkId), reviewData)
        .then(response => {
          console.log('Framework review submitted successfully:', response.data);
          console.log('Response data details:', {
            ApprovalId: response.data.ApprovalId,
            Version: response.data.Version,
            ApprovedNot: response.data.ApprovedNot,
            ApprovedDate: response.data.ApprovedDate
          });
          
          // Reset loading state
          this.isSubmittingRejection = false;
          
          // Update the approval data with the response
          this.selectedApproval.ApprovedNot = approved;
          this.selectedApproval.Version = response.data.Version;
          
          if (approved) {
            this.selectedApproval.ExtractedData.Status = 'Approved';
            
            // Store the approval date from the response
            if (response.data.ApprovedDate) {
              this.selectedApproval.ApprovedDate = response.data.ApprovedDate;
            }
            
            // Update all policies and subpolicies to Approved status in the UI
            if (this.selectedApproval.ExtractedData.policies) {
              this.selectedApproval.ExtractedData.policies.forEach(policy => {
                policy.Status = 'Approved';
                
                if (policy.subpolicies) {
                  policy.subpolicies.forEach(subpolicy => {
                    subpolicy.Status = 'Approved';
                  });
                }
              });
            }
            
            PopupService.success('Framework approved successfully!', 'Framework Approved');
          } else {
            this.selectedApproval.ExtractedData.Status = 'Rejected';
            console.log('Framework rejected - updating UI state');
            PopupService.success('Framework rejected successfully!', 'Framework Rejected');
          }
          
          // Refresh the frameworks list
          console.log('Refreshing frameworks list after review submission');
          this.fetchFrameworks();
          this.fetchRejectedFrameworks();
        })
        .catch(error => {
          this.handleError(error, 'submitting framework review');
          // Reset loading state on error
          this.isSubmittingRejection = false;
        });
    },
    
    async fetchRejectedFrameworks() {
      console.log('Fetching rejected frameworks...');
      
      // Determine which user ID to use for API calls
      const userIdForAPI = this.selectedUserId || this.currentUserId;
      console.log('Using user ID for rejected frameworks:', userIdForAPI);
      
      if (!userIdForAPI) {
        console.warn('No user ID available for fetching rejected frameworks');
        return Promise.resolve();
      }
      
      // Use the selected user ID or current user ID for fetching rejected frameworks
      return axios.get(API_ENDPOINTS.FRAMEWORKS_REJECTED, {
        params: { user_id: userIdForAPI }
      })
        .then(response => {
          console.log('Rejected frameworks response:', response.data);
          console.log('Number of rejected frameworks:', response.data.length);
          
          let processedFrameworks = response.data.map(framework => {
            // Make sure framework data is properly structured
            if (!framework.ExtractedData) {
              framework.ExtractedData = {};
            }
            
            // Add ReviewerId and CreatedBy to ExtractedData for consistent filtering
            if (framework.ReviewerId) {
              framework.ExtractedData.Reviewer = framework.ReviewerId;
              framework.ExtractedData.ReviewerName = framework.Reviewer;
            }
            if (framework.CreatedBy) {
              framework.ExtractedData.CreatedBy = framework.CreatedBy;
            }
            
            console.log('Processing rejected framework:', {
              FrameworkId: framework.FrameworkId,
              ApprovalId: framework.ApprovalId,
              Status: framework.ExtractedData?.Status,
              ApprovedNot: framework.ApprovedNot,
              ReviewerId: framework.ReviewerId,
              CreatedBy: framework.CreatedBy
            });
            return framework;
          });
          
          // Filter by selected framework if one is selected
          if (this.selectedFrameworkId) {
            console.log('🔍 DEBUG: Filtering rejected frameworks by selected framework ID:', this.selectedFrameworkId);
            processedFrameworks = processedFrameworks.filter(framework => 
              framework.FrameworkId.toString() === this.selectedFrameworkId.toString()
            );
            console.log('✅ DEBUG: Filtered rejected frameworks count:', processedFrameworks.length);
          }
          
          this.rejectedFrameworks = processedFrameworks;
          console.log('Final rejected frameworks count:', this.rejectedFrameworks.length);
          console.log('Final rejected frameworks data:', this.rejectedFrameworks);
          
          if (this.rejectedFrameworks.length === 0) {
            console.warn('⚠️ No rejected frameworks found for user:', userIdForAPI);
            console.warn('⚠️ This could mean:');
            console.warn('   1. The user has no rejected frameworks');
            console.warn('   2. The frameworks Status field is not set to "Rejected"');
            console.warn('   3. The CreatedByName field does not match the user ID or username');
          }
        })
        .catch(error => {
          console.error('❌ Error fetching rejected frameworks:', error);
          if (error.response) {
            console.error('❌ Response data:', error.response.data);
            console.error('❌ Response status:', error.response.status);
          }
        });
    },
    
    openRejectedItem(framework) {
      console.log('Opening rejected framework for editing:', framework);
      this.editingFramework = JSON.parse(JSON.stringify(framework)); // Deep copy
      
      // Store the original data for change detection
      this.originalFrameworkData = JSON.parse(JSON.stringify(framework.ExtractedData || {}));
      
      // Ensure the framework has the proper structure for editing
      if (!this.editingFramework.ExtractedData) {
        this.editingFramework.ExtractedData = {};
      }
      
      // Ensure policies array exists
      if (!this.editingFramework.ExtractedData.policies) {
        console.warn('No policies found in rejected framework, initializing empty policies array');
        this.editingFramework.ExtractedData.policies = [];
        } else {
        console.log(`Found ${this.editingFramework.ExtractedData.policies.length} policies in framework`);
        
        // Process each policy
        this.editingFramework.ExtractedData.policies.forEach(policy => {
          // Initialize policy category fields if they don't exist
          if (!policy.PolicyType) policy.PolicyType = '';
          if (!policy.PolicyCategory) policy.PolicyCategory = '';
          if (!policy.PolicySubCategory) policy.PolicySubCategory = '';
          
          console.log(`Policy ${policy.PolicyId} category fields:`, {
            PolicyType: policy.PolicyType,
            PolicyCategory: policy.PolicyCategory,
            PolicySubCategory: policy.PolicySubCategory
          });
          
          // Ensure each policy has subpolicies array
          if (!policy.subpolicies) {
            policy.subpolicies = [];
          }
        });
      }
      
      this.showEditModal = true;
    },
    
    closeEditModal() {
      this.showEditModal = false;
      this.editingFramework = null;
      this.originalFrameworkData = null; // Clear original data
    },
    
    resubmitFramework(framework) {
      const frameworkId = this.getFrameworkId(framework);
      console.log('Resubmitting framework with ID:', frameworkId);
      console.log('Framework data before preparing:', framework);
      
      // Check if any changes were made to the framework
      const hasChanges = this.checkFrameworkChanges(framework);
      if (!hasChanges) {
        // Don't show popup since we have inline warning now
        return;
      }
      
      // Validate framework data
      const validationErrors = this.validateFrameworkData(framework);
      if (validationErrors.length > 0) {
        PopupService.warning(`Please fix the following errors before resubmitting:\n${validationErrors.join('\n')}`, 'Validation Errors');
        return;
      }
      
      // Check if policies exist and have proper structure
      if (framework.ExtractedData.policies && framework.ExtractedData.policies.length > 0) {
        // Ensure each policy has the correct fields
        framework.ExtractedData.policies.forEach((policy, index) => {
          console.log(`Checking policy ${index} with ID: ${policy.PolicyId}`);
          console.log(`Policy category fields:`, {
            PolicyType: policy.PolicyType,
            PolicyCategory: policy.PolicyCategory,
            PolicySubCategory: policy.PolicySubCategory
          });
          
          // Ensure subpolicies are properly formatted
          if (policy.subpolicies && policy.subpolicies.length > 0) {
            policy.subpolicies.forEach((subpolicy, subIndex) => {
              console.log(`Checking subpolicy ${subIndex} with ID: ${subpolicy.SubPolicyId}`);
              
              // Make sure required fields exist
              if (!subpolicy.SubPolicyName) {
                console.warn(`SubpolicyName is missing for subpolicy ${subIndex} in policy ${index}`);
              }
              if (!subpolicy.Description) {
                console.warn(`Description is missing for subpolicy ${subIndex} in policy ${index}`);
              }
            });
      } else {
            console.log(`Policy ${index} has no subpolicies or they are not properly structured`);
          }
        });
      } else {
        console.warn('No policies found in framework data or policies array is not properly structured');
      }
      
      // Prepare data for resubmission
      const resubmitData = {
        FrameworkName: framework.ExtractedData.FrameworkName,
        FrameworkDescription: framework.ExtractedData.FrameworkDescription,
        Category: framework.ExtractedData.Category,
        EffectiveDate: framework.ExtractedData.EffectiveDate,
        StartDate: framework.ExtractedData.StartDate,
        EndDate: framework.ExtractedData.EndDate,
        policies: framework.ExtractedData.policies ? framework.ExtractedData.policies.map(policy => {
          // Log each policy's category fields before mapping
          console.log(`Processing policy ${policy.PolicyId} for resubmission with category fields:`, {
            PolicyType: policy.PolicyType,
            PolicyCategory: policy.PolicyCategory,
            PolicySubCategory: policy.PolicySubCategory
          });
          
          // Ensure all policy fields are included, especially the category fields
          const mappedPolicy = {
            ...policy,
            PolicyId: policy.PolicyId,
            PolicyName: policy.PolicyName,
            PolicyDescription: policy.PolicyDescription,
            Status: policy.Status,
            StartDate: policy.StartDate,
            EndDate: policy.EndDate,
            Department: policy.Department,
            Objective: policy.Objective,
            Scope: policy.Scope,
            Applicability: policy.Applicability,
            Identifier: policy.Identifier,
            CoverageRate: policy.CoverageRate,
            // Explicitly include category fields with fallbacks
            PolicyType: policy.PolicyType || '',
            PolicyCategory: policy.PolicyCategory || '',
            PolicySubCategory: policy.PolicySubCategory || '',
            subpolicies: policy.subpolicies || []
          };
          
          return mappedPolicy;
        }) : []
      };
      
      console.log('Prepared resubmission data:', resubmitData);
      console.log('Policies in resubmission data:', resubmitData.policies);
      console.log('Number of policies:', resubmitData.policies.length);
      
      // Submit resubmission request
      console.log('Final resubmission data to be sent:', JSON.stringify(resubmitData));
      
      // Add explicit logging for policy category fields
      if (resubmitData.policies && resubmitData.policies.length > 0) {
        console.log('CRITICAL - Policy category fields in final resubmission data:');
        resubmitData.policies.forEach((policy, index) => {
          // Ensure policy category fields are properly set (not undefined)
          policy.PolicyType = policy.PolicyType || '';
          policy.PolicyCategory = policy.PolicyCategory || '';
          policy.PolicySubCategory = policy.PolicySubCategory || '';
          
          console.log(`Policy ${index} (${policy.PolicyId}):`, {
            PolicyType: policy.PolicyType,
            PolicyCategory: policy.PolicyCategory,
            PolicySubCategory: policy.PolicySubCategory
          });
        });
      }
      
      axios.put(API_ENDPOINTS.FRAMEWORK_RESUBMIT_APPROVAL(frameworkId), resubmitData)
        .then(response => {
          console.log('Framework resubmitted successfully:', response.data);
          
          // Show version information in the alert
          PopupService.success('Framework resubmitted for review!', 'Framework Resubmitted');
          
          this.closeEditModal();
          this.fetchRejectedFrameworks();
          this.fetchFrameworks();
        })
        .catch(error => {
          console.error('Error data:', error.response ? error.response.data : 'No response data');
          this.handleError(error, 'resubmitting framework');
        });
    },
    
    // Check if any changes were made to the framework
    checkFrameworkChanges(framework) {
      console.log('Checking for framework changes...');
      
      // Get the original rejected version for comparison
      // We need to compare against the original rejected data, not the current data
      const originalData = this.originalFrameworkData || framework.ExtractedData || {};
      const rejectionReason = this.getRejectionReason(framework);
      
      // Check if any main framework fields have been modified
      const mainFieldsChanged = (
        originalData.FrameworkName !== framework.ExtractedData?.FrameworkName ||
        originalData.FrameworkDescription !== framework.ExtractedData?.FrameworkDescription ||
        originalData.Category !== framework.ExtractedData?.Category ||
        originalData.EffectiveDate !== framework.ExtractedData?.EffectiveDate ||
        originalData.StartDate !== framework.ExtractedData?.StartDate ||
        originalData.EndDate !== framework.ExtractedData?.EndDate
      );
      
      // Check if any policies have been modified
      let policiesChanged = false;
      if (originalData.policies && Array.isArray(originalData.policies)) {
        for (let i = 0; i < originalData.policies.length; i++) {
          const originalPolicy = originalData.policies[i];
          const currentPolicy = framework.ExtractedData?.policies?.[i];
          
          if (currentPolicy) {
            if (originalPolicy.PolicyName !== currentPolicy.PolicyName ||
                originalPolicy.PolicyDescription !== currentPolicy.PolicyDescription ||
                originalPolicy.Scope !== currentPolicy.Scope ||
                originalPolicy.Objective !== currentPolicy.Objective ||
                originalPolicy.Department !== currentPolicy.Department ||
                originalPolicy.Applicability !== currentPolicy.Applicability) {
              policiesChanged = true;
              break;
            }
            
            // Check subpolicies within each policy
            if (originalPolicy.subpolicies && currentPolicy.subpolicies) {
              for (let j = 0; j < originalPolicy.subpolicies.length; j++) {
                const originalSubpolicy = originalPolicy.subpolicies[j];
                const currentSubpolicy = currentPolicy.subpolicies[j];
                
                if (currentSubpolicy) {
                  if (originalSubpolicy.Description !== currentSubpolicy.Description ||
                      originalSubpolicy.Control !== currentSubpolicy.Control ||
                      originalSubpolicy.SubPolicyName !== currentSubpolicy.SubPolicyName) {
                    policiesChanged = true;
                    break;
                  }
                }
              }
            }
          }
        }
      }
      
      // Check if rejection reason has been addressed (this counts as a change)
      const rejectionAddressed = rejectionReason && rejectionReason.trim() !== '';
      
      const hasChanges = mainFieldsChanged || policiesChanged || rejectionAddressed;
      
      console.log('Framework change detection results:', {
        mainFieldsChanged,
        policiesChanged,
        rejectionAddressed,
        hasChanges
      });
      
      return hasChanges;
    },
    
    // Get rejection reason for framework
    getRejectionReason(framework) {
      // Check all possible locations for rejection reason
      if (framework.rejectionReason && framework.rejectionReason !== 'No rejection reason provided') {
        return framework.rejectionReason;
      }
      
      if (framework.ExtractedData?.rejection_reason) {
        return framework.ExtractedData.rejection_reason;
      }
      
      if (framework.ExtractedData?.framework_approval?.remarks) {
        return framework.ExtractedData.framework_approval.remarks;
      }
      
      return '';
    },
    
    formatFieldName(field) {
      // Convert camelCase or PascalCase to display format
      return field
        // Insert space before all uppercase letters
        .replace(/([A-Z])/g, ' $1')
        // Replace first char with uppercase
        .replace(/^./, str => str.toUpperCase())
        .trim();
    },
    
    approvePolicy(policy) {
      if (!this.selectedApproval || !this.selectedApproval.FrameworkId) {
        console.error('No framework selected for policy approval');
        return;
      }

      // Check if all subpolicies are approved
      if (policy.subpolicies && policy.subpolicies.length > 0) {
        const allSubpoliciesApproved = policy.subpolicies.every(sub => sub.Status === 'Approved');
        if (!allSubpoliciesApproved) {
          PopupService.warning('All subpolicies must be approved before approving the policy', 'Subpolicies Not Approved');
          return;
        }
      }

      const frameworkId = this.getFrameworkId(this.selectedApproval);

      // Call backend endpoint
      axios.put(API_ENDPOINTS.FRAMEWORK_POLICY_APPROVE_REJECT(frameworkId, policy.PolicyId), {
        approved: true,
        submit_review: false // Don't submit review automatically
      })
        .then(response => {
          console.log('Policy approved successfully:', response.data);

          // Update policy status
          policy.Status = 'Approved';

          // Check if all policies are approved to update framework status
          const allPoliciesApproved = this.selectedApproval.ExtractedData.policies.every(p => 
            p.Status === 'Approved' || (p.subpolicies && p.subpolicies.every(sub => sub.Status === 'Approved'))
          );

          if (allPoliciesApproved) {
            this.selectedApproval.ExtractedData.Status = 'Ready for Final Approval';
          }

          PopupService.success('Policy approved successfully!', 'Policy Approved');
        })
        .catch(error => {
          this.handleError(error, 'approving policy');
        });
    },
    
    rejectPolicy(policy) {
      if (!this.selectedApproval || !this.selectedApproval.FrameworkId) {
        console.error('No framework selected for policy rejection');
        return;
      }
      
      this.currentRejectionType = 'policy';
      this.currentRejectionItem = policy;
      this.showRejectModal = true;
    },
    
    rejectSubpolicy(policy, subpolicy) {
      if (!this.selectedApproval || !this.selectedApproval.FrameworkId) {
        console.error('No framework selected for subpolicy rejection');
        return;
      }
      
      this.currentRejectionType = 'subpolicy';
      this.currentRejectionItem = { policy, subpolicy };
      this.showRejectModal = true;
    },
    
    canApprovePolicy(policy) {
      // Can't approve if already approved or rejected
      if (policy.Status === 'Approved' || policy.Status === 'Rejected') {
        return false;
      }

      // If policy has subpolicies, all must be approved
      if (policy.subpolicies && policy.subpolicies.length > 0) {
        return policy.subpolicies.every(sub => sub.Status === 'Approved');
      }

      // If no subpolicies, can approve
      return true;
    },
    
    approveSubpolicy(policy, subpolicy) {
      if (!this.selectedApproval || !this.selectedApproval.FrameworkId) {
        console.error('No framework selected for subpolicy approval');
        return;
      }
      
      const frameworkId = this.getFrameworkId(this.selectedApproval);
      
      // Call backend endpoint
      axios.put(API_ENDPOINTS.FRAMEWORK_POLICY_SUBPOLICY_APPROVE_REJECT(frameworkId, policy.PolicyId, subpolicy.SubPolicyId), {
          approved: true,
        submit_review: false // Don't submit review automatically
      })
        .then(response => {
          console.log('Subpolicy approved successfully:', response.data);
          
          // Update subpolicy status
          subpolicy.Status = 'Approved';
          
          // Check if all subpolicies in this policy are approved
          const allSubpoliciesApproved = policy.subpolicies && 
            policy.subpolicies.every(sp => sp.Status === 'Approved');
          
          if (allSubpoliciesApproved) {
            // Update policy status to indicate it's ready for approval
            policy.Status = 'Ready for Approval';
            PopupService.success('All subpolicies approved. Policy is now ready for approval.', 'Subpolicies Approved');
          } else {
            PopupService.success('Subpolicy approved successfully!', 'Subpolicy Approved');
          }
        })
        .catch(error => {
          this.handleError(error, 'approving subpolicy');
        });
    },
    
    areAllSubpoliciesApproved(policy) {
      if (!policy.subpolicies || policy.subpolicies.length === 0) return true;
      return policy.subpolicies.every(subpolicy => subpolicy.Status === 'Approved');
    },
    
    areAllPoliciesApproved() {
      if (!this.selectedApproval?.ExtractedData?.policies) return false;
      
      return this.selectedApproval.ExtractedData.policies.every(policy => {
        // Check policy status
        if (policy.Status !== 'Approved') {
          // If not approved, check if all subpolicies are approved
          return policy.subpolicies && policy.subpolicies.every(sub => sub.Status === 'Approved');
        }
        return true;
      });
    },
    
    getFrameworkApprovalStatus() {
      if (!this.selectedApproval || !this.selectedApproval.ExtractedData) return 'Unknown';
      
      const policies = this.selectedApproval.ExtractedData.policies || [];
      if (policies.length === 0) return 'No Policies';
      
      const approvedCount = policies.filter(p => p.Status === 'Approved').length;
      const rejectedCount = policies.filter(p => p.Status === 'Rejected').length;
      const totalCount = policies.length;
      
      if (rejectedCount > 0) {
        return `Rejected (${rejectedCount}/${totalCount} policies rejected)`;
      } else if (approvedCount === totalCount) {
        return `Ready for Final Approval (${approvedCount}/${totalCount} policies approved)`;
      } else {
        return `Under Review (${approvedCount}/${totalCount} policies approved)`;
      }
    },
    
    canApproveFramework() {
      if (!this.selectedApproval || !this.selectedApproval.ExtractedData) return false;
      if (this.selectedApproval.ApprovedNot !== null) return false; // Already approved/rejected
      
      // Check if all policies are approved
      return this.areAllPoliciesApproved();
    },
    
    approveEntireFramework() {
      if (!this.selectedApproval || !this.selectedApproval.FrameworkId) {
        console.error('No framework selected for entire framework approval');
        return;
      }
      
      if (!this.canApproveFramework()) {
        PopupService.warning('All policies must be approved before approving the framework', 'Policies Not Approved');
        return;
      }
      
      PopupService.confirm(
        'Are you sure you want to give final approval to this entire framework?',
        'Confirm Final Approval',
        () => {
          this.proceedWithFrameworkApproval();
        }
      );
    },
    
    proceedWithFrameworkApproval() {
      
      const frameworkId = this.getFrameworkId(this.selectedApproval);
      
      // Call backend endpoint for final framework approval
      axios.put(API_ENDPOINTS.FRAMEWORK_APPROVE_FINAL(frameworkId))
        .then(response => {
          console.log('Framework approved successfully:', response.data);
          
          // Update framework status and store approval date
          this.selectedApproval.ExtractedData.Status = 'Approved';
          this.selectedApproval.ApprovedNot = true;
          
          // Store the approval date from the response
          if (response.data.ApprovedDate) {
            this.selectedApproval.ApprovedDate = response.data.ApprovedDate;
          }
          
          // Update all policies and subpolicies to Approved status
          if (this.selectedApproval.ExtractedData.policies) {
            this.selectedApproval.ExtractedData.policies.forEach(policy => {
              policy.Status = 'Approved';
              
              if (policy.subpolicies) {
                policy.subpolicies.forEach(subpolicy => {
                  subpolicy.Status = 'Approved';
                });
              }
            });
          }
          
          PopupService.success('Framework approved successfully!', 'Framework Approved');
          
          // Refresh the frameworks list
          this.fetchFrameworks();
        })
        .catch(error => {
          this.handleError(error, 'approving entire framework');
        });
    },
    
    // Update the existing submitReview method to use our helper method
    submitReview() {
      console.log('submitReview called with approval:', this.selectedApproval);
      
      // Prevent submission if framework is already processed (approved or rejected)
      if (this.selectedApproval && this.selectedApproval.ExtractedData?.Status === 'Rejected') {
        console.log('Framework is already rejected, preventing duplicate submission');
        PopupService.warning('Framework has already been rejected and cannot be submitted again.', 'Already Rejected');
        return;
      }
      
      if (this.selectedApproval && this.selectedApproval.ExtractedData?.Status === 'Approved') {
        console.log('Framework is already approved, preventing duplicate submission');
        PopupService.warning('Framework has already been approved and cannot be submitted again.', 'Already Approved');
        return;
      }
      
      if (this.selectedApproval && this.selectedApproval.ApprovedNot !== null) {
        console.log('Delegating to submitFrameworkReview with approval status:', this.selectedApproval.ApprovedNot);
        this.submitFrameworkReview(this.selectedApproval.ApprovedNot);
      } else {
        console.error('Cannot submit review - no approval or approval status set');
      }
    },
    
    // Helper method to validate framework data before submission
    validateFrameworkData(framework) {
      const validationErrors = [];
      
      // Check required framework fields
      if (!framework.ExtractedData.FrameworkName) {
        validationErrors.push('Framework Name is required');
      }
      
      if (!framework.ExtractedData.FrameworkDescription) {
        validationErrors.push('Framework Description is required');
      }
      
      // Check policies if they exist
      if (framework.ExtractedData.policies && framework.ExtractedData.policies.length > 0) {
        framework.ExtractedData.policies.forEach((policy, index) => {
          if (!policy.PolicyName) {
            validationErrors.push(`Policy #${index + 1} is missing a name`);
          }
          
          // Log policy category fields to help with debugging
          console.log(`Validating policy #${index + 1} category fields:`, {
            PolicyType: policy.PolicyType,
            PolicyCategory: policy.PolicyCategory,
            PolicySubCategory: policy.PolicySubCategory
          });
          
          // Check subpolicies if they exist
          if (policy.subpolicies && policy.subpolicies.length > 0) {
            policy.subpolicies.forEach((subpolicy, subIndex) => {
              if (!subpolicy.SubPolicyName) {
                validationErrors.push(`Subpolicy #${subIndex + 1} in Policy "${policy.PolicyName || `#${index + 1}`}" is missing a name`);
              }
            });
          }
        });
      }
      
      return validationErrors;
    },
    
    fetchPolicyTypes() {
      console.log('Fetching policy categories...');
      axios.get(API_ENDPOINTS.POLICY_CATEGORIES)
        .then(response => {
          console.log('Policy categories response:', response.data);
          // Store the raw categories data
          this.policyCategories = response.data;
          
          // Create a structured map for easier filtering
          const typeMap = {};
          
          // Process the categories into a nested structure
          response.data.forEach(category => {
            if (!typeMap[category.PolicyType]) {
              typeMap[category.PolicyType] = {
                categories: {}
              };
            }
            
            if (!typeMap[category.PolicyType].categories[category.PolicyCategory]) {
              typeMap[category.PolicyType].categories[category.PolicyCategory] = {
                subCategories: []
              };
            }
            
            typeMap[category.PolicyType].categories[category.PolicyCategory].subCategories.push(
              category.PolicySubCategory
            );
          });
          
          this.policyCategoriesMap = typeMap;
          console.log('Processed policy categories map:', this.policyCategoriesMap);
        })
        .catch(error => {
          console.error('Error fetching policy categories:', error);
        });
    },
    
    // Helper method to initialize or update policy category fields
    initializePolicyCategoryFields(policy) {
      console.log(`Initializing policy category fields for policy: ${policy.PolicyId || 'New Policy'}`);
      
      // Log current values
      console.log('Current policy category fields:', {
        PolicyType: policy.PolicyType,
        PolicyCategory: policy.PolicyCategory,
        PolicySubCategory: policy.PolicySubCategory
      });
      
      // If policy type changes, reset category and subcategory
      this.$watch(() => policy.PolicyType, (newType, oldType) => {
        if (newType !== oldType) {
          console.log(`Policy type changed from ${oldType} to ${newType}, resetting category and subcategory`);
          policy.PolicyCategory = '';
          policy.PolicySubCategory = '';
        }
      });
      
      // If policy category changes, reset subcategory
      this.$watch(() => policy.PolicyCategory, (newCategory, oldCategory) => {
        if (newCategory !== oldCategory) {
          console.log(`Policy category changed from ${oldCategory} to ${newCategory}, resetting subcategory`);
          policy.PolicySubCategory = '';
        }
      });
      
      return policy;
    },
    
    // Handle policy type change
    handlePolicyTypeChange(policy) {
      console.log(`Policy type changed to: ${policy.PolicyType}`);
      // Reset dependent fields when type changes
      policy.PolicyCategory = '';
      policy.PolicySubCategory = '';
    },
    
    // Handle policy category change
    handlePolicyCategoryChange(policy) {
      console.log(`Policy category changed to: ${policy.PolicyCategory}`);
      // Reset subcategory when category changes
      policy.PolicySubCategory = '';
    },

    // Add new methods for CollapsibleTable
    toggleSection(sectionName) {
      this.expandedSections[sectionName] = !this.expandedSections[sectionName];
    },
    mapFrameworkToTableRow(framework) {
    return {
        id: this.getFrameworkId(framework),
        name: framework.ExtractedData.FrameworkName,
        category: framework.ExtractedData.Category || 'No Category',
        createdBy: framework.ExtractedData.CreatedByName || 'System',
        createdDate: this.formatDate(framework.ExtractedData.CreatedByDate || framework.created_at),
        actions: 'VIEW DETAILS',
        // Store original framework data for reference
        originalData: framework
      };
    },
    getStatusBadge(framework) {
      const status = framework.ApprovedNot === true ? 'Approved' :
                    framework.ApprovedNot === false ? 'Rejected' : 'Pending';
      return `<span class="status-badge ${status.toLowerCase()}">${status}</span>`;
    },
    sortRejected(key) {
      if (this.rejectedSortConfig.key === key) {
        this.rejectedSortConfig.direction = 
          this.rejectedSortConfig.direction === 'asc' ? 'desc' : 'asc';
      } else {
        this.rejectedSortConfig.key = key;
        this.rejectedSortConfig.direction = 'asc';
      }
    },
    
    checkPolicyApprovalStatus(policy) {
      if (!policy.subpolicies || policy.subpolicies.length === 0) return;
      
      const allSubpoliciesApproved = policy.subpolicies.every(sub => sub.Status === 'Approved');
      if (allSubpoliciesApproved) {
        policy.Status = 'Approved';
      }
    },
    
    getStatusClass(status) {
      return {
        'status-approved': status === 'Approved',
        'status-rejected': status === 'Rejected',
        'status-pending': status === 'Under Review' || !status
      };
    },

    // Helper method to check if review can be submitted
    canSubmitReview(framework) {
      if (!framework || !framework.ExtractedData) return false;
      
      // Can only submit review if framework is under review and not already processed
      return framework.ExtractedData.Status === 'Under Review' && 
             framework.ApprovedNot === null;
    },

    // Helper method to get tooltip for submit button
    getSubmitButtonTooltip(framework) {
      if (!framework || !framework.ExtractedData) return 'Cannot submit review';
      
      if (framework.ExtractedData.Status === 'Approved') {
        return 'Framework is already approved';
      } else if (framework.ExtractedData.Status === 'Rejected') {
        return 'Framework is already rejected';
      } else if (framework.ApprovedNot !== null) {
        return 'Review decision already made';
      } else {
        return 'Submit your review decision';
      }
    },

    // Helper method to check if framework belongs to current user's tasks
    isMyFramework(framework) {
      const currentUserId = this.selectedUserId || this.currentUserId;
      if (!currentUserId) return false;
      
      // Check if framework was created by the current user
      // Compare by user ID (most reliable) or by user name as fallback
      const createdBy = framework.ExtractedData?.CreatedBy;
      const createdByName = framework.ExtractedData?.CreatedByName;
      
      // Check by ID first (most reliable)
      if (createdBy && String(createdBy) === String(currentUserId)) {
        return true;
      }
      
      // Fallback to name comparison if ID not available
      if (createdByName && createdByName === this.getCurrentUserName()) {
        return true;
      }
      
      return false;
    },

    // Helper method to check if framework is assigned for review
    isReviewerFramework(framework) {
      const currentUserId = this.selectedUserId || this.currentUserId;
      if (!currentUserId) {
        console.log(`⚠️ No currentUserId in isReviewerFramework for framework ${framework.FrameworkId}`);
        return false;
      }
      
      // For GRC Administrators viewing a specific user, check if that user is the reviewer
      if (this.isGRCAdministrator && this.selectedUserId) {
        const isReviewer = framework.ReviewerId === this.selectedUserId ||
                          framework.ExtractedData?.Reviewer === this.selectedUserId;
        console.log(`🔍 GRC Admin checking framework ${framework.FrameworkId} for user ${this.selectedUserId}:`, {
          reviewerId: framework.ReviewerId,
          extractedReviewer: framework.ExtractedData?.Reviewer,
          isReviewer: isReviewer
        });
        return isReviewer;
      }
      
      // For regular users, show frameworks assigned to them for review
      const isReviewerById = framework.ReviewerId === currentUserId;
      const isReviewerByExtracted = framework.ExtractedData?.Reviewer === currentUserId;
      
      console.log(`🔍 Checking if framework ${framework.FrameworkId} is reviewer task for user ${currentUserId}:`, {
        reviewerId: framework.ReviewerId,
        extractedReviewer: framework.ExtractedData?.Reviewer,
        currentUserId: currentUserId,
        isReviewerById: isReviewerById,
        isReviewerByExtracted: isReviewerByExtracted,
        result: isReviewerById || isReviewerByExtracted
      });
      
      return isReviewerById || isReviewerByExtracted;
    },

    // Helper method to get current user name
    getCurrentUserName() {
      if (this.selectedUserId && this.availableUsers.length > 0) {
        const selectedUser = this.availableUsers.find(u => u.UserId === this.selectedUserId);
        return selectedUser ? selectedUser.UserName : '';
      }
      // For current user, use stored username or fallback to localStorage
      return this.currentUserName || localStorage.getItem('user_name') || '';
    }
  },
  watch: {
    // Watch for user initialization to complete
    userInitialized(newVal) {
      if (newVal) {
        console.log('✅ User initialized, current user ID:', this.currentUserId);
        console.log('✅ User initialized, current user name:', this.currentUserName);
        console.log('✅ User initialized, is GRC Admin:', this.isGRCAdministrator);
      }
    },
    // Watch for current user ID changes
    currentUserId(newVal, oldVal) {
      console.log('🔄 Current user ID changed from', oldVal, 'to', newVal);
      if (newVal && this.userInitialized) {
        // Force re-evaluation of reviewer permissions
        this.$forceUpdate();
      }
    }
  },
  computed: {
    pendingApprovalsCount() {
      // Calculate from actual task data (both myTasks and reviewerTasks)
      const myPending = this.myTasks?.filter(t => t.ApprovedNot === null || t.ApprovedNot === undefined).length || 0;
      const reviewerPending = this.reviewerTasks?.filter(t => t.ApprovedNot === null || t.ApprovedNot === undefined).length || 0;
      return myPending + reviewerPending;
    },
    approvedApprovalsCount() {
      // Calculate from actual task data (both myTasks and reviewerTasks)
      const myApproved = this.myTasks?.filter(t => t.ApprovedNot === true).length || 0;
      const reviewerApproved = this.reviewerTasks?.filter(t => t.ApprovedNot === true).length || 0;
      return myApproved + reviewerApproved;
    },
    rejectedApprovalsCount() {
      // Calculate from actual task data (both myTasks and reviewerTasks)
      const myRejected = this.myTasks?.filter(t => t.ApprovedNot === false).length || 0;
      const reviewerRejected = this.reviewerTasks?.filter(t => t.ApprovedNot === false).length || 0;
      // Also include rejected frameworks that can be edited and resubmitted
      const rejectedFrameworksCount = this.rejectedFrameworks?.length || 0;
      return myRejected + reviewerRejected + rejectedFrameworksCount;
    },
    hasFrameworkChanges() {
      if (!this.editingFramework) return false;
      return this.checkFrameworkChanges(this.editingFramework);
    },
    sortedFrameworks() {
      return [...this.approvals].sort((a, b) => {
        const dateA = new Date(a.ExtractedData?.CreatedByDate || 0);
        const dateB = new Date(b.ExtractedData?.CreatedByDate || 0);
        return dateB - dateA; // Most recent first
      });
    },
    policyTypeOptions() {
      // Get unique policy types from the structured map
      return Object.keys(this.policyCategoriesMap);
    },
    filteredPolicyCategories() {
      return (policyType) => {
        if (!policyType || !this.policyCategoriesMap[policyType]) return [];
        // Get categories for the selected policy type
        return Object.keys(this.policyCategoriesMap[policyType].categories);
      };
    },
    filteredPolicySubCategories() {
      return (policyType, policyCategory) => {
        if (!policyType || !policyCategory || 
            !this.policyCategoriesMap[policyType] || 
            !this.policyCategoriesMap[policyType].categories[policyCategory]) {
          return [];
        }
        // Get subcategories for the selected policy type and category
        return this.policyCategoriesMap[policyType].categories[policyCategory].subCategories;
      };
    },
    sortedRejectedFrameworks() {
      return [...this.rejectedFrameworks].sort((a, b) => {
        const key = this.rejectedSortConfig.key;
        let aValue = key.includes('.') ? 
          key.split('.').reduce((obj, k) => obj?.[k], a) : 
          a[key];
        let bValue = key.includes('.') ? 
          key.split('.').reduce((obj, k) => obj?.[k], b) : 
          b[key];
        
        // Handle dates
        if (key === 'CreatedByDate') {
          aValue = new Date(aValue || 0);
          bValue = new Date(bValue || 0);
        }
        
        // Handle strings
        if (typeof aValue === 'string') {
          aValue = aValue.toLowerCase();
          bValue = bValue.toLowerCase();
        }
        
        if (this.rejectedSortConfig.direction === 'asc') {
          return aValue > bValue ? 1 : -1;
        } else {
          return aValue < bValue ? 1 : -1;
        }
      });
    },
    myTasksSections() {
      const sections = [
        {
          name: 'Under Review',
          statusClass: 'pending',
          tasks: this.myTasks
            .filter(f => f.ApprovedNot === null)
            .map(this.mapFrameworkToTableRow)
        },
        {
          name: 'Approved',
          statusClass: 'approved',
          tasks: this.myTasks
            .filter(f => f.ApprovedNot === true)
            .map(this.mapFrameworkToTableRow)
        },
        {
          name: 'Rejected',
          statusClass: 'rejected',
          tasks: this.myTasks
            .filter(f => f.ApprovedNot === false)
            .map(this.mapFrameworkToTableRow)
        }
      ];
      return sections;
    },
    reviewerTasksSections() {
      const sections = [
        {
          name: 'Under Review',
          statusClass: 'pending',
          tasks: this.reviewerTasks
            .filter(f => f.ApprovedNot === null)
            .map(this.mapFrameworkToTableRow)
        },
        {
          name: 'Approved',
          statusClass: 'approved',
          tasks: this.reviewerTasks
            .filter(f => f.ApprovedNot === true)
            .map(this.mapFrameworkToTableRow)
        },
        {
          name: 'Rejected',
          statusClass: 'rejected',
          tasks: this.reviewerTasks
            .filter(f => f.ApprovedNot === false)
            .map(this.mapFrameworkToTableRow)
        }
      ];
      return sections;
    },
    myTasksCount() {
      return this.myTasks.length;
    },
    reviewerTasksCount() {
      return this.reviewerTasks.length;
    },
    
    // Computed property to filter frameworks - show only the selected framework
    filteredFrameworks() {
      if (this.selectedFrameworkId) {
        // If a framework is selected, show only that framework
        const selectedFramework = this.frameworks.find(f => f.id.toString() === this.selectedFrameworkId.toString());
        return selectedFramework ? [selectedFramework] : [];
      } else {
        // If no framework is selected, show all frameworks
        return this.frameworks;
      }
    }
  }
}
</script>

<style scoped>
@import './FrameworkApprover.css';

/* Override modal header and close button styles with higher specificity */
.edit-framework-modal .edit-framework-content .modal-header {
  background: transparent !important;
  background-color: transparent !important;
}

.edit-framework-modal .edit-framework-content .modal-header h3 {
  background: transparent !important;
  background-color: transparent !important;
  color: #212529 !important;
}

.edit-framework-modal .edit-framework-content .close-btn {
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  padding: 0 !important;
  width: auto !important;
  height: auto !important;
  min-width: auto !important;
  min-height: auto !important;
  box-shadow: none !important;
  color: #4a5568 !important;
  font-size: 24px !important;
  font-weight: normal !important;
}

.edit-framework-modal .edit-framework-content .close-btn:hover {
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: #212529 !important;
}

/* Main container adjustments for sidebar */
.framework_main_container {
  margin-left: 250px;
  width: calc(100% - 250px);
  transition: margin-left 0.3s ease, width 0.3s ease;
  min-height: 100vh;
  background-color: transparent !important;
  background: transparent !important;
  padding: 20px;
  box-shadow: none !important;
  border: none !important;
}

/* Framework Selection Dropdown Styles */
.framework-selection-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #f8f9fa;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #e9ecef;
  margin-bottom: 15px;
}

.framework-select-label {
  font-weight: 500;
  color: #495057;
  margin: 0;
  white-space: nowrap;
}

.framework-select-dropdown {
  padding: 6px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  background-color: white;
  font-size: 14px;
  min-width: 200px;
  cursor: pointer;
}

.framework-select-dropdown:focus {
  outline: none;
  border-color: #80bdff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.framework-select-dropdown option {
  padding: 8px;
}

.framework-help-text {
  display: block;
  margin-top: 6px;
  font-size: 0.8rem;
  color: #64748b;
  font-style: italic;
}


/* User Selection Dropdown Styles */
.dashboard-controls {
  display: flex;
  align-items: center;
  gap: 2rem;
  flex-wrap: wrap;
}

/* Enhanced form control styling to match Policy Approver */
.dashboard-controls .form-control {
  width: 300px;
  min-width: 250px;
  max-width: 350px;
  background: #ffffff;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
  transition: all 0.3s ease;
}

.dashboard-controls .form-control:hover {
  border-color: #6366f1;
  box-shadow: 0 8px 15px rgba(99, 102, 241, 0.1), 0 3px 6px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.dashboard-controls .form-control:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15), 0 8px 15px rgba(99, 102, 241, 0.1);
  transform: translateY(-1px);
  background: #ffffff;
}

/* Enhanced label styling for user selection */
.dashboard-controls label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #1e293b;
  font-size: 14px;
}

/* User help text styling */
.user-help-text {
  display: block;
  margin-top: 8px;
  color: #64748b;
  font-size: 12px;
  font-style: italic;
  padding: 6px 12px;
  background: #ffffff;
  border-radius: 6px;
  border-left: 3px solid #6366f1;
}

/* Info Cards Styles */
.no-user-selected-message {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  margin: 2rem 0;
}

.info-card {
  background: #ffffff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 3rem;
  text-align: center;
  max-width: 500px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.info-card i {
  font-size: 3rem;
  color: #6c757d;
  margin-bottom: 1rem;
}

.info-card h3 {
  color: #495057;
  margin-bottom: 1rem;
  font-size: 1.5rem;
  font-weight: 600;
}

.info-card p {
  color: #6c757d;
  margin-bottom: 0;
  line-height: 1.5;
}


/* Add new styles for table integration */
.frameworks-table-container {
  margin-top: 2rem;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 500;
  display: inline-block;
}

.status-badge.pending {
  background-color: #ffffff;
  color: #92400e;
}

.status-badge.approved {
  background-color: #ffffff;
  color: #065f46;
}

.status-badge.rejected {
  background-color: #ffffff;
  color: #991b1b;
}

/* Add new styles for rejected frameworks table */
.rejected-approvals-section {
  margin-top: 2rem;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
}

.table-container {
  overflow-x: auto;
  margin-top: 1rem;
}

.frameworks-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.frameworks-table th {
  background: transparent !important;
  padding: 12px 16px;
  font-weight: 600;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #374151;
  border-bottom: 2px solid #e5e7eb;
  cursor: pointer;
  user-select: none;
}

.frameworks-table th i {
  margin-left: 4px;
  font-size: 0.75rem;
  color: #9ca3af;
}

.frameworks-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  color: #1f2937;
}

.framework-id-link {
  color: #2563eb;
  text-decoration: none;
  font-weight: 500;
}

.framework-id-link:hover {
  text-decoration: underline;
}

.actions-cell {
  white-space: nowrap;
}

.view-btn, .edit-btn {
  padding: 6px 12px;
  margin: 0 4px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.view-btn {
  background: #ffffff;
  color: #374151;
}

.edit-btn {
  background: #ffffff;
  color: white;
}

.view-btn:hover {
  background: #ffffff;
}

.edit-btn:hover {
  background: #ffffff;
}

.status-badge.rejected {
  background-color: #ffffff;
  color: #991b1b;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
}

/* Add/update styles for subpolicy actions */
.subpolicy-actions {
  display: flex;
  gap: 8px;
  margin-left: 12px;
}

.approve-subpolicy-btn,
.reject-subpolicy-btn {
  padding: 6px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  transition: all 0.2s ease;
}

.approve-subpolicy-btn {
  background-color: #ffffff;
  color: white;
}

.reject-subpolicy-btn {
  background-color: #ffffff;
  color: white;
}

.approve-subpolicy-btn:hover:not(:disabled) {
  background-color: #ffffff;
}

.reject-subpolicy-btn:hover:not(:disabled) {
  background-color: #ffffff;
}

.approve-subpolicy-btn:disabled,
.reject-subpolicy-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.subpolicy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background-color: #ffffff;
  border-radius: 4px 4px 0 0;
}

.subpolicy-header-actions {
  display: flex;
  align-items: center;
}

.subpolicy-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
}

.subpolicy-status.status-approved {
  background-color: #ffffff;
  color: #166534;
}

.subpolicy-status.status-rejected {
  background-color: #ffffff;
  color: #991b1b;
}

.subpolicy-status.status-pending {
  background-color: #ffffff;
  color: #92400e;
}

.subpolicy-item {
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  margin-bottom: 12px;
}

.subpolicy-details {
  padding: 12px;
  background-color: #ffffff;
  border-radius: 0 0 4px 4px;
}

.subpolicy-detail-item {
  margin-bottom: 8px;
}

.subpolicy-detail-item:last-child {
  margin-bottom: 0;
}

/* Tab Navigation Styles */
.tab-navigation {
  display: flex;
  justify-content: flex-start;
  gap: 2rem;
  margin-bottom: 2rem;
  border-bottom: none;
  background: transparent;
  border-radius: 0;
  padding: 0;
}

.tab-button {
  background: transparent;
  border: none;
  font-size: 1rem;
  font-weight: 600;
  color: #6c757d;
  cursor: pointer;
  padding: 1rem 2rem;
  transition: all 0.3s ease;
  border-radius: 0;
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  white-space: nowrap;
}

.tab-button:hover {
  background: transparent;
  color: #495057;
}

.tab-button.active {
  background: transparent;
  color: #2563eb;
  border-bottom: 3px solid #2563eb;
  margin-bottom: -2px;
}

.tab-button i {
  font-size: 0.9rem;
}

/* Tab Content Styles */
.tab-content {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  min-height: auto;
}

.tab-panel {
  padding: 0 !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 0 !important;
}

/* Remove all card styling from tab-related elements */
.tab-content * {
  background: transparent !important;
  box-shadow: none !important;
  border: none !important;
  border-radius: 0 !important;
}

/* Ensure all table elements have transparent backgrounds */
.task-section,
.task-section-header,
.task-table,
.task-table th,
.task-table td,
.task-table tbody tr {
  background: transparent !important;
  box-shadow: none !important;
}

/* Creator message styles */
.creator-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background-color: #ffffff;
  border: 1px solid #2196f3;
  border-radius: 6px;
  color: #1976d2;
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.creator-message i {
  color: #2196f3;
  font-size: 1rem;
}

.creator-message span {
  font-weight: 500;
}

.creator-message-small {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background-color: #ffffff;
  border: 1px solid #2196f3;
  border-radius: 4px;
  color: #1976d2;
  font-size: 0.8rem;
  margin-left: 0.5rem;
}

.creator-message-small i {
  color: #2196f3;
  font-size: 0.8rem;
}

/* Admin message styles */
.admin-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background-color: #ffffff;
  border: 1px solid #ff9800;
  border-radius: 6px;
  color: #e65100;
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.admin-message i {
  color: #ff9800;
  font-size: 1rem;
}

.admin-message span {
  font-weight: 500;
}

/* Processed framework message styles */
.processed-framework-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background-color: #ffffff;
  border: 1px solid #0ea5e9;
  border-radius: 6px;
  color: #0369a1;
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.processed-framework-message i {
  color: #0ea5e9;
  font-size: 1rem;
}

.processed-framework-message span {
  font-weight: 500;
}

/* Responsive adjustments for sidebar */
@media (max-width: 1024px) {
  .framework_main_container {
    margin-left: 0;
    width: 100%;
  }
}

@media (max-width: 768px) {
  .framework_main_container {
    margin-left: 0;
    width: 100%;
    padding: 10px;
  }
  
  .dashboard-controls {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .dashboard-controls .form-control {
    width: 100%;
    min-width: 100%;
    max-width: 100%;
  }
  
  .tab-navigation {
    flex-direction: column;
    gap: 0;
  }
  
  .tab-button {
    width: 100%;
    justify-content: center;
    border-radius: 0;
  }
  
  .tab-button:first-child {
    border-radius: 8px 8px 0 0;
  }
  
  .tab-button:last-child {
    border-radius: 0 0 8px 8px;
  }
}
</style> 