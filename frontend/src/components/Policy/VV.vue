<template>
  <div class="VV-page-wrapper">
    <div class="VV-page-header">
      <h2>Policy Versioning</h2>
    </div>
    
    <p class="vv-intro-text-description">Create and manage versions of your frameworks and policies to track changes over time.</p>
    
    <div class="vv-info-cards">
      <div class="vv-info-card">
        <div class="vv-info-card-icon">
          <i class="fas fa-code-branch"></i>
        </div>
        <div class="vv-info-card-content">
          <h3>Version Control</h3>
          <p>Track changes to frameworks and policies with complete version history.</p>
        </div>
      </div>
      <div class="vv-info-card">
        <div class="vv-info-card-icon">
          <i class="fas fa-history"></i>
        </div>
        <div class="vv-info-card-content">
          <h3>Change Management</h3>
          <p>Document and review changes between different versions of your policies.</p>
        </div>
      </div>
      <div class="vv-info-card">
        <div class="vv-info-card-icon">
          <i class="fas fa-tasks"></i>
        </div>
        <div class="vv-info-card-content">
          <h3>Compliance Tracking</h3>
          <p>Ensure your organization maintains compliance as regulations evolve over time.</p>
        </div>
      </div>
    </div>
    <div class="VV-toggle-group">
      <button :class="['VV-toggle', { 'VV-active': selectedTab === 'framework' } ]" @click="selectTab('framework')">Framework</button>
      <button :class="['VV-toggle', { 'VV-active': selectedTab === 'policy' } ]" @click="selectTab('policy')">Policy</button>
      </div>
    <div v-if="selectedTab === 'framework'" class="VV-top-dropdowns">
      <div v-if="error" class="VV-error-message">
        <i class="fas fa-exclamation-triangle"></i>
        {{ error }}
        <button @click="refreshFrameworks" class="VV-retry-btn">Retry</button>
      </div>
      <CustomDropdown
        v-model="selectedFramework"
        :config="{
          label: 'Framework',
          values: selectedFramework ? frameworks.filter(fw => String(fw.id) === String(selectedFramework)).map(fw => ({ value: String(fw.id), label: fw.name })) : frameworks.map(fw => ({ value: String(fw.id), label: fw.name })),
          defaultLabel: frameworks.length === 0 ? 'No frameworks available' : 'Select Framework'
        }"
        :showSearchBar="true"
        style="min-width: 300px; max-width: 360px; width: 340px;"
        :disabled="frameworks.length === 0 || loading"
      />
      </div>
    <div v-else class="VV-top-dropdowns">
      <div v-if="error" class="VV-error-message">
        <i class="fas fa-exclamation-triangle"></i>
        {{ error }}
        <button @click="refreshFrameworks" class="VV-retry-btn">Retry</button>
      </div>
      <CustomDropdown
        v-model="selectedFramework"
        :config="{
          label: 'Framework',
          values: selectedFramework ? frameworks.filter(fw => String(fw.id) === String(selectedFramework)).map(fw => ({ value: String(fw.id), label: fw.name })) : frameworks.map(fw => ({ value: String(fw.id), label: fw.name })),
          defaultLabel: frameworks.length === 0 ? 'No frameworks available' : 'Select Framework'
        }"
        :showSearchBar="true"
        style="min-width: 300px; max-width: 360px; width: 360px;"
        :disabled="frameworks.length === 0 || loading"
      />
      <CustomDropdown
        v-model="selectedPolicy"
        :config="{
          label: 'Policy',
          values: policies.map(pol => ({ value: pol.id, label: pol.name })),
          defaultLabel: policies.length === 0 ? 'No policies available' : 'Select Policy'
        }"
        :showSearchBar="true"
        style="min-width: 300px; max-width: 360px; width: 360px;"
        :disabled="policies.length === 0 || !selectedFramework || loading"
      />
      </div>
    <div v-if="selectedTab === 'framework' && selectedFramework">
      <div class="VV-container">
        <!-- Framework Form -->
        <form @submit.prevent="submitFramework">
          <div class="VV-form-group">
            <label class="VV-label">FRAMEWORK NAME *</label>
            <input class="VV-input" v-model="frameworkForm.name" type="text" required placeholder="Enter Framework name" />
            <small class="VV-desc">Enter a descriptive name for your framework</small>
              </div>
          <div class="VV-form-group">
            <label class="VV-label">DESCRIPTION *</label>
            <textarea class="VV-textarea" v-model="frameworkForm.description" rows="3" required placeholder="Enter framework description"></textarea>
            <small class="VV-desc">Describe the purpose, scope, and objectives of this framework</small>
            </div>
          <div class="VV-row">
            <div class="VV-form-group VV-half">
              <label class="VV-label">IDENTIFIER * <span class="auto-generated-label">(Auto-generated)</span></label>
              <input class="VV-input" v-model="frameworkForm.identifier" type="text" required placeholder="Enter Identifier" readonly />
              <small class="VV-desc">Auto-generated based on framework name</small>
          </div>
            <div class="VV-form-group VV-half">
              <label class="VV-label">CATEGORY *</label>
              <input class="VV-input" v-model="frameworkForm.category" type="text" required placeholder="Enter category" />
              <small class="VV-desc">e.g., Security, Compliance, Risk Management, etc.</small>
              </div>
                </div>
          <div class="VV-row">
            <div class="VV-form-group VV-half">
              <label class="VV-label">INTERNAL/EXTERNAL *</label>
              <select class="VV-input" v-model="frameworkForm.internalExternal" required>
                <option value="" disabled>Select Type</option>
                    <option value="Internal">Internal</option>
                    <option value="External">External</option>
                  </select>
              <small class="VV-desc">Select whether this framework is for internal or external use</small>
                </div>
            <div class="VV-form-group VV-half">
              <label class="VV-label">UPLOAD DOCUMENT</label>
              <input class="VV-input" type="file" @change="handleFileUpload" />
              <small class="VV-desc">Upload a supporting document for this framework (optional)</small>
                  </div>
                </div>
          <div class="VV-row">
            <div class="VV-form-group VV-half">
              <label class="VV-label">EFFECTIVE START DATE *</label>
              <input class="VV-input" v-model="frameworkForm.startDate" type="date" required />
              <small class="VV-desc">Date when the framework implementation begins</small>
              </div>
            <div class="VV-form-group VV-half">
              <label class="VV-label">EFFECTIVE END DATE *</label>
              <input class="VV-input" v-model="frameworkForm.endDate" type="date" required />
              <small class="VV-desc">Date when the framework expires or requires review</small>
                </div>
                </div>
        <div class="VV-row">
          <div class="VV-form-group VV-half">
            <label class="VV-label">CREATED BY *</label>
            <input class="VV-input" :value="currentUser.UserName || loggedInUsername" type="text" disabled />
            <small class="VV-desc">Automatically set to logged in user</small>
          </div>
          <div class="VV-form-group VV-half">
            <label class="VV-label">REVIEWER *</label>
            <select class="VV-input" v-model="frameworkForm.reviewer" required>
              <option value="">Select Reviewer</option>
              <option v-for="user in users" :key="user.id" :value="user.id">{{ user.name }}</option>
            </select>
            <small class="VV-desc">Select who will review this framework</small>
            <div v-if="isFrameworkCreatorReviewerSame" class="VV-error-text">
              <i class="fas fa-exclamation-triangle"></i>
              Creator and reviewer cannot be the same person. Please select a different reviewer.
            </div>
          </div>
        </div>
        </form>
            </div>
      <!-- Policy Tabbed/Stepper Container (Framework Mode) -->
      <div class="VV-policy-tabs-container">
        <div class="VV-policy-tabs-row">
          <div class="VV-policy-tabs">
            <button v-for="(tab, idx) in policyTabs" :key="tab.id" :class="['VV-policy-tab', { 'VV-policy-tab-active': idx === activePolicyTab, 'excluded': tab.exclude }]" @click="activePolicyTab = idx">
              Policy {{ idx + 1 }}
            </button>
            <button class="VV-add-policy-tab" @click="addPolicyTab">+ Add Policy</button>
              </div>
            </div>
        <div v-if="policyTabs.length && policyTabs[activePolicyTab]" class="VV-policy-form-container">
          <button 
            class="VV-exclude-policy-btn" 
            @click="excludePolicyTab(activePolicyTab)"
            :class="{ 'excluded': policyTabs[activePolicyTab].exclude }"
          >
            {{ policyTabs[activePolicyTab].exclude ? 'Include' : 'Exclude' }}
          </button>
          <div v-if="policyTabs[activePolicyTab].exclude" class="TT-excluded-message">
            This policy has been excluded and will not be included in the submission.
          </div>
          <!-- Hide form when policy is excluded -->
          <form v-else @submit.prevent="submitPolicy(activePolicyTab)" :key="policyTabs[activePolicyTab].id">
            <div class="VV-row">
              <div class="VV-form-group VV-half">
                <label class="VV-label">POLICY NAME *</label>
                <input class="VV-input" v-model="policyTabs[activePolicyTab].name" type="text" required placeholder="Enter policy name" @input="handlePolicyNameChange(activePolicyTab, $event.target.value)" />
                <small class="VV-desc">Use a clear, descriptive name</small>
          </div>
              <div class="VV-form-group VV-half">
                <label class="VV-label">POLICY IDENTIFIER * 
                  <span v-if="isInternalFramework()" class="auto-generated-label">(Auto-generated)</span>
                  <span v-else class="manual-entry-label">(Manual entry)</span>
                </label>
                <input class="VV-input" v-model="policyTabs[activePolicyTab].identifier" type="text" required placeholder="Enter policy identifier" :readonly="isInternalFramework()" />
                <small class="VV-desc">{{ isInternalFramework() ? 'Auto-generated based on policy name' : 'Enter a unique identifier for this policy' }}</small>
        </div>
            </div>
            <div class="VV-form-group">
              <label class="VV-label">DESCRIPTION *</label>
              <textarea class="VV-textarea" v-model="policyTabs[activePolicyTab].description" rows="3" required placeholder="Enter policy description"></textarea>
              <small class="VV-desc">Describe the policy's purpose, requirements, and key provisions</small>
          </div>
            <div class="VV-row">
              <div class="VV-form-group VV-half">
                <label class="VV-label">SCOPE *</label>
                <input class="VV-input" v-model="policyTabs[activePolicyTab].scope" type="text" required placeholder="Enter policy scope" />
                <small class="VV-desc">Specify what areas/processes/systems policy applies to</small>
            </div>
              <div class="VV-form-group VV-half">
                <label class="VV-label">DEPARTMENT *</label>
                <div class="VV-searchable-select">
                  <input 
                    class="VV-input" 
                    v-model="policyTabs[activePolicyTab].department" 
                    type="text" 
                    required 
                    placeholder="Search or enter new department"
                    list="departments"
                    @input="handleDepartmentChange(activePolicyTab, $event.target.value)"
                  />
                  <datalist id="departments">
                    <option v-for="dept in departments" :key="dept.id" :value="dept.name">
                      {{ dept.name }}
                    </option>
                  </datalist>
                </div>
                <small class="VV-desc">Select from list or type new department name</small>
          </div>
              </div>
            <div class="VV-form-group">
              <label class="VV-label">OBJECTIVE *</label>
              <textarea class="VV-textarea" v-model="policyTabs[activePolicyTab].objective" rows="3" required placeholder="Enter policy objective"></textarea>
              <small class="VV-desc">Explain what this policy is designed to accomplish</small>
                </div>
            <div class="VV-row">
              <div class="VV-form-group VV-half">
                <label class="VV-label">COVERAGE RATE (%) *</label>
                <input class="VV-input" v-model="policyTabs[activePolicyTab].coverageRate" type="number" min="0" max="100" step="0.01" required placeholder="Enter coverage rate" />
                <small class="VV-desc">Range: 0-100, step: 0.01</small>
                </div>
              <div class="VV-form-group VV-half">
                <label class="VV-label">APPLICABILITY *</label>
                <input class="VV-input" v-model="policyTabs[activePolicyTab].applicability" type="text" required placeholder="Enter applicability" />
                <small class="VV-desc">Define the target audience, roles, or entities</small>
              </div>
              </div>
            <div class="VV-row">
              <div class="VV-form-group VV-half">
                <label class="VV-label">POLICY TYPE *</label>
                <div class="policy-type-multi-select" @click.stop>
                  <div class="policy-type-dropdown">
                    <div   
                      class="selected-policy-type" 
                      :class="{ active: policyTabs[activePolicyTab].showPolicyTypeDropdown }"
                      @click="togglePolicyTypeDropdown(activePolicyTab)"
                    >
                      <div class="policy-type-content">
                        <span v-if="policyTabs[activePolicyTab].type" class="policy-type-value">
                          {{ policyTabs[activePolicyTab].type }}
                        </span>
                        <span v-else class="placeholder">
                          Search or enter new policy type
                        </span>
                      </div>
                      <i class="fas fa-chevron-down dropdown-arrow"></i>
                    </div>
                    <div v-if="policyTabs[activePolicyTab].showPolicyTypeDropdown" class="policy-type-options">
                      <!-- Search Input -->
                      <div class="search-input-container">
                        <input
                          v-model="policyTabs[activePolicyTab].policyTypeSearch"
                          type="text"
                          placeholder="Search or type new policy type..."
                          class="search-input"
                          @input="filterPolicyTypes()"
                          @keyup.enter="createNewPolicyType(activePolicyTab)"
                        />
                      </div>
                      <!-- Existing Options -->
                      <div 
                        v-for="type in getFilteredPolicyTypes(activePolicyTab)" 
                        :key="type" 
                        class="policy-type-option"
                        @click="selectPolicyType(activePolicyTab, type)"
                      >
                        <span class="policy-type-label">{{ type }}</span>
                      </div>
                      <!-- Create New Option -->
                      <div 
                        v-if="policyTabs[activePolicyTab].policyTypeSearch && !getFilteredPolicyTypes(activePolicyTab).includes(policyTabs[activePolicyTab].policyTypeSearch)"
                        class="policy-type-option create-new-option"
                        @click="createNewPolicyType(activePolicyTab)"
                      >
                        <i class="fas fa-plus"></i>
                        <span class="policy-type-label">Create "{{ policyTabs[activePolicyTab].policyTypeSearch }}"</span>
                      </div>
                    </div>
                  </div>
                </div>
                <small class="VV-desc">Select from list or type new policy type</small>
              </div>
              <div class="VV-form-group VV-half">
                <label class="VV-label">POLICY CATEGORY *</label>
                <div class="policy-category-multi-select" @click.stop>
                  <div class="policy-category-dropdown">
                    <div   
                      class="selected-policy-category" 
                      :class="{ active: policyTabs[activePolicyTab].showPolicyCategoryDropdown }"
                      @click="togglePolicyCategoryDropdown(activePolicyTab)"
                    >
                      <div class="policy-category-content">
                        <span v-if="policyTabs[activePolicyTab].category" class="policy-category-value">
                          {{ policyTabs[activePolicyTab].category }}
                        </span>
                        <span v-else class="placeholder">
                          Search or enter new policy category
                        </span>
                      </div>
                      <i class="fas fa-chevron-down dropdown-arrow"></i>
                    </div>
                    <div v-if="policyTabs[activePolicyTab].showPolicyCategoryDropdown" class="policy-category-options">
                      <!-- Search Input -->
                      <div class="search-input-container">
                        <input
                          v-model="policyTabs[activePolicyTab].policyCategorySearch"
                          type="text"
                          placeholder="Search or type new policy category..."
                          class="search-input"
                          @input="filterPolicyCategories()"
                          @keyup.enter="createNewPolicyCategory(activePolicyTab)"
                        />
                      </div>
                      <!-- Existing Options -->
                      <div 
                        v-for="category in getFilteredPolicyCategories(activePolicyTab)" 
                        :key="category" 
                        class="policy-category-option"
                        @click="selectPolicyCategory(activePolicyTab, category)"
                      >
                        <span class="policy-category-label">{{ category }}</span>
                      </div>
                      <!-- Create New Option -->
                      <div 
                        v-if="policyTabs[activePolicyTab].policyCategorySearch && !getFilteredPolicyCategories(activePolicyTab).includes(policyTabs[activePolicyTab].policyCategorySearch)"
                        class="policy-category-option create-new-option"
                        @click="createNewPolicyCategory(activePolicyTab)"
                      >
                        <i class="fas fa-plus"></i>
                        <span class="policy-category-label">Create "{{ policyTabs[activePolicyTab].policyCategorySearch }}"</span>
                      </div>
                    </div>
                  </div>
                </div>
                <small class="VV-desc">Select from list or type new policy category</small>
              </div>
            </div>
            <div class="VV-row">
              <div class="VV-form-group VV-half">
                <label class="VV-label">POLICY SUB CATEGORY *</label>
                <div class="policy-subcategory-multi-select" @click.stop>
                  <div class="policy-subcategory-dropdown">
                    <div   
                      class="selected-policy-subcategory" 
                      :class="{ active: policyTabs[activePolicyTab].showPolicySubCategoryDropdown }"
                      @click="togglePolicySubCategoryDropdown(activePolicyTab)"
                    >
                      <div class="policy-subcategory-content">
                        <span v-if="policyTabs[activePolicyTab].subCategory" class="policy-subcategory-value">
                          {{ policyTabs[activePolicyTab].subCategory }}
                        </span>
                        <span v-else class="placeholder">
                          Search or enter new policy sub category
                        </span>
                      </div>
                      <i class="fas fa-chevron-down dropdown-arrow"></i>
                    </div>
                    <div v-if="policyTabs[activePolicyTab].showPolicySubCategoryDropdown" class="policy-subcategory-options">
                      <!-- Search Input -->
                      <div class="search-input-container">
                        <input
                          v-model="policyTabs[activePolicyTab].policySubCategorySearch"
                          type="text"
                          placeholder="Search or type new policy sub category..."
                          class="search-input"
                          @input="filterPolicySubCategories()"
                          @keyup.enter="createNewPolicySubCategory(activePolicyTab)"
                        />
                      </div>
                      <!-- Existing Options -->
                      <div 
                        v-for="subCategory in getFilteredPolicySubCategories(activePolicyTab)" 
                        :key="subCategory" 
                        class="policy-subcategory-option"
                        @click="selectPolicySubCategory(activePolicyTab, subCategory)"
                      >
                        <span class="policy-subcategory-label">{{ subCategory }}</span>
                      </div>
                      <!-- Create New Option -->
                      <div 
                        v-if="policyTabs[activePolicyTab].policySubCategorySearch && !getFilteredPolicySubCategories(activePolicyTab).includes(policyTabs[activePolicyTab].policySubCategorySearch)"
                        class="policy-subcategory-option create-new-option"
                        @click="createNewPolicySubCategory(activePolicyTab)"
                      >
                        <i class="fas fa-plus"></i>
                        <span class="policy-subcategory-label">Create "{{ policyTabs[activePolicyTab].policySubCategorySearch }}"</span>
                      </div>
                    </div>
                  </div>
                </div>
                <small class="VV-desc">Select from list or type new policy sub category</small>
              </div>
              <div class="VV-form-group VV-half">
                <label class="VV-label">APPLICABLE ENTITIES *</label>
              <div class="form-row">
                <div class="form-group entities-group">
                  <div class="entities-multi-select" @click.stop>
                    <div class="entities-dropdown">
                      <div 
                        class="selected-entities" 
                        :class="{ 
                          'active': policyTabs[activePolicyTab]?.showEntitiesDropdown,
                          'error': error && error.includes('entities')
                        }"
                        @click="toggleEntitiesDropdown(activePolicyTab)"
                      >
                        <div class="entity-content">
                          <span v-if="loading" class="loading-text">
                            Loading entities...
                          </span>
                          <span v-else-if="isAllEntitiesSelected(activePolicyTab)" class="entity-tag all-tag">
                            All Locations
                          </span>
                          <span v-else-if="getSelectedEntitiesCount(activePolicyTab) === 0" class="placeholder">
                            Select entities...
                          </span>
                          <span v-else class="entity-count">
                            {{ getSelectedEntitiesCount(activePolicyTab) }} location(s) selected
                          </span>
                        </div>
                        <i class="fas fa-chevron-down dropdown-arrow"></i>
                      </div>
                      <div v-if="policyTabs[activePolicyTab]?.showEntitiesDropdown" class="entities-options">
                        <div v-if="loading" class="entities-loading">
                          Loading entities...
                        </div>
                        <div v-else-if="error" class="entities-error">
                          {{ error }}
                        </div>
                        <template v-else>
                          <div 
                            v-for="entity in entities" 
                            :key="entity.id" 
                            :class="['entity-option', { 'all-option': entity.id === 'all' }]"
                            @click="selectEntity(activePolicyTab, entity.id)"
                          >
                            <input 
                              type="checkbox" 
                              :checked="entity.id === 'all' ? isAllEntitiesSelected(activePolicyTab) : isEntitySelected(activePolicyTab, entity.id)"
                              @change="handleEntitySelection(activePolicyTab, entity.id, $event.target.checked)"
                              @click.stop
                            />
                            <span class="entity-label">{{ entity.label }}</span>
                          </div>
                        </template>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
                <small class="VV-desc">Select the locations/entities this policy applies to</small>
                </div>
                </div>
            <div class="VV-row">
              <div class="VV-form-group VV-half">
                <label class="VV-label">START DATE *</label>
                <input class="VV-input" v-model="policyTabs[activePolicyTab].startDate" type="date" required />
                <small class="VV-desc">Date when this policy takes effect</small>
              </div>
              <div class="VV-form-group VV-half">
                <label class="VV-label">END DATE *</label>
                <input class="VV-input" v-model="policyTabs[activePolicyTab].endDate" type="date" required />
                <small class="VV-desc">Date when this policy expires or requires review/renewal</small>
                  </div>
                </div>
            <!-- Show CreatedByName and Reviewer only in policy tab -->
            <div v-if="selectedTab === 'policy'" class="VV-row">
              <div class="VV-form-group VV-half">
                <label class="VV-label">CREATED BY *</label>
                <input class="VV-input" :value="currentUser.UserName || loggedInUsername" type="text" disabled />
                <small class="VV-desc">Automatically set to logged in user</small>
              </div>
              <div class="VV-form-group VV-half">
                <label class="VV-label">REVIEWER *</label>
                <select 
                  class="VV-input" 
                  v-model="policyTabs[activePolicyTab].reviewer" 
                  required
                >
                  <option value="">Select Reviewer</option>
                  <option v-for="user in users" :key="user.id" :value="user.id">{{ user.name }}</option>
                </select>
                <small class="VV-desc">Select who will review this policy</small>
                <div v-if="isPolicyCreatorReviewerSame" class="VV-error-text" style="border: 3px solid red !important; background: yellow !important;">
                  <i class="fas fa-exclamation-triangle"></i>
                  Creator and reviewer cannot be the same person. Please select a different reviewer.
                </div>

                  </div>
                </div>
            <div class="VV-form-group">
              <label class="VV-label">UPLOAD DOCUMENT</label>
              <input class="VV-input" type="file" @change="e => handlePolicyFileUpload(e, activePolicyTab)" />
              <small class="VV-desc">Upload supporting documentation (optional)</small>
                  </div>
          </form>
                </div>
              </div>
      <div v-if="policyTabs.length && policyTabs[activePolicyTab]" class="VV-subpolicy-tabs-container">
        <div class="VV-subpolicy-tabs-row">
          <div class="VV-subpolicy-tabs">
            <button v-for="(subTab, subIdx) in policyTabs[activePolicyTab].subPolicies" :key="subTab.id" :class="['VV-subpolicy-tab', { 'VV-subpolicy-tab-active': subIdx === policyTabs[activePolicyTab].activeSubPolicyTab, 'excluded': subTab.exclude }]" @click="policyTabs[activePolicyTab].activeSubPolicyTab = subIdx">
              Subpolicy {{ subIdx + 1 }}
            </button>
            <button class="VV-add-subpolicy-tab" @click="addSubPolicyTab(activePolicyTab)">+ Add Sub Policy</button>
                  </div>
                </div>
        <div v-if="policyTabs[activePolicyTab].subPolicies && policyTabs[activePolicyTab].subPolicies.length" class="VV-subpolicy-form-container">
          <button 
            class="VV-exclude-subpolicy-btn" 
            @click="excludeSubPolicyTab(activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
            :class="{ 'excluded': policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].exclude }"
          >
            {{ policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].exclude ? 'Include' : 'Exclude' }}
          </button>
          <div v-if="policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].exclude" class="TT-excluded-message">
            This subpolicy has been excluded and will not be included in the submission.
          </div>
          <!-- Hide form when subpolicy is excluded -->
          <form v-else>
            <div class="VV-form-group">
              <label class="VV-label">SUB POLICY NAME *</label>
              <input class="VV-input" v-model="policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].name" type="text" required placeholder="Enter sub policy name" @input="handleSubPolicyNameChange(activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab, $event.target.value)" />
              <small class="VV-desc">Use a clear name that describes this sub-policy's specific focus</small>
                        </div>
            <div class="VV-form-group">
              <label class="VV-label">IDENTIFIER * 
                <span v-if="isInternalFramework()" class="auto-generated-label">(Auto-generated)</span>
                <span v-else class="manual-entry-label">(Manual entry)</span>
              </label>
              <input class="VV-input" v-model="policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].identifier" type="text" required placeholder="Enter identifier" :readonly="isInternalFramework()" />
              <small class="VV-desc">{{ isInternalFramework() ? 'Auto-generated based on parent policy identifier' : 'Enter a unique identifier for this sub-policy' }}</small>
                      </div>
            <div class="VV-form-group">
              <label class="VV-label">CONTROL *</label>
              <textarea class="VV-textarea" v-model="policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].control" rows="3" required placeholder="Enter control"></textarea>
              <small class="VV-desc">Specify the control mechanisms, procedures, or safeguards to be implemented</small>
                        </div>
            <div class="VV-form-group">
              <label class="VV-label">DESCRIPTION *</label>
              <textarea class="VV-textarea" v-model="policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].description" rows="3" required placeholder="Enter description"></textarea>
              <small class="VV-desc">Explain the intent, requirements, or significance of this sub-policy</small>
                      </div>
          </form>
                    </div>
                  </div>
                </div>
    <div v-else-if="selectedTab === 'framework' && !selectedFramework">
      <!-- Optionally, you can show a message here: Please select a framework -->
    </div>
    <!-- Version Type Modal Popup -->
    <div v-if="showVersionModal" class="version-modal-overlay" @click="showVersionModal = false">
      <div class="version-modal" @click.stop>
        <h2>Version Type</h2>
        <div class="version-type-options">
          <label class="version-type-option">
            <input type="radio" value="minor" v-model="selectedVersionType" />
            <span class="radio-custom" :class="{ checked: selectedVersionType === 'minor' }"></span>
            <span class="version-type-title">Minor Version</span>
            <span class="version-type-desc">Incremental changes and improvements<br/><span class="version-type-example">Example: 1.0 → 1.1</span></span>
          </label>
          <label class="version-type-option">
            <input type="radio" value="major" v-model="selectedVersionType" />
            <span class="radio-custom" :class="{ checked: selectedVersionType === 'major' }"></span>
            <span class="version-type-title">Major Version</span>
            <span class="version-type-desc">Significant changes or overhauls<br/><span class="version-type-example">Example: 1.5 → 2.0</span></span>
          </label>
        </div>
        <div class="version-modal-actions">
          <button class="btn-primary" @click.prevent="confirmVersionType">OK</button>
          <button class="btn-secondary" @click.prevent="showVersionModal = false">Cancel</button>
        </div>
      </div>
    </div>
    <div v-if="selectedTab === 'policy' && selectedFramework && selectedPolicy">
      <div class="VV-policy-tabs-container">
        <div class="VV-policy-tabs-row">
          <div class="VV-policy-tabs">
            <button v-for="(tab, idx) in policyTabs" :key="tab.id" :class="['VV-policy-tab', { 'VV-policy-tab-active': idx === activePolicyTab, 'excluded': tab.exclude }]" @click="activePolicyTab = idx">
              Policy {{ idx + 1 }}
            </button>
            <!-- Only show + Add Policy in framework mode -->
            <button v-if="selectedTab === 'framework'" class="VV-add-policy-tab" @click="addPolicyTab">+ Add Policy</button>
              </div>
                </div>
        <div v-if="policyTabs.length && policyTabs[activePolicyTab]" class="VV-policy-form-container">
          <!-- Only show Exclude in framework mode -->
          <button v-if="selectedTab === 'framework'" class="VV-exclude-policy-btn" @click="excludePolicyTab(activePolicyTab)">Exclude</button>
          <form @submit.prevent="submitPolicy(activePolicyTab)" :key="policyTabs[activePolicyTab].id">
            <!-- Same policy form as above -->
            <div class="VV-row">
              <div class="VV-form-group VV-half">
                <label class="VV-label">POLICY NAME *</label>
                <input class="VV-input" v-model="policyTabs[activePolicyTab].name" type="text" required placeholder="Enter policy name" @input="handlePolicyNameChange(activePolicyTab, $event.target.value)" />
                <small class="VV-desc">Use a clear, descriptive name</small>
                </div>
              <div class="VV-form-group VV-half">
                <label class="VV-label">POLICY IDENTIFIER * <span class="auto-generated-label">(Auto-generated)</span></label>
                <input class="VV-input" v-model="policyTabs[activePolicyTab].identifier" type="text" required placeholder="Enter policy identifier" readonly />
                <small class="VV-desc">Auto-generated based on policy name</small>
              </div>
              </div>
            <div class="VV-form-group">
              <label class="VV-label">DESCRIPTION *</label>
              <textarea class="VV-textarea" v-model="policyTabs[activePolicyTab].description" rows="3" required placeholder="Enter policy description"></textarea>
              <small class="VV-desc">Describe the policy's purpose, requirements, and key provisions</small>
            </div>
            <div class="VV-row">
              <div class="VV-form-group VV-half">
                <label class="VV-label">SCOPE *</label>
                <input class="VV-input" v-model="policyTabs[activePolicyTab].scope" type="text" required placeholder="Enter policy scope" />
                <small class="VV-desc">Specify what areas/processes/systems policy applies to</small>
              </div>
              <div class="VV-form-group VV-half">
                <label class="VV-label">DEPARTMENT *</label>
                <div class="VV-searchable-select">
                  <input 
                    class="VV-input" 
                    v-model="policyTabs[activePolicyTab].department" 
                    type="text" 
                    required 
                    placeholder="Search or enter new department"
                    list="departments"
                    @input="handleDepartmentChange(activePolicyTab, $event.target.value)"
                  />
                  <datalist id="departments">
                    <option v-for="dept in departments" :key="dept.id" :value="dept.name">
                      {{ dept.name }}
                    </option>
                  </datalist>
                </div>
                <small class="VV-desc">Select from list or type new department name</small>
                </div>
              </div>
            <div class="VV-form-group">
              <label class="VV-label">OBJECTIVE *</label>
              <textarea class="VV-textarea" v-model="policyTabs[activePolicyTab].objective" rows="3" required placeholder="Enter policy objective"></textarea>
              <small class="VV-desc">Explain what this policy is designed to accomplish</small>
                </div>
            <div class="VV-row">
              <div class="VV-form-group VV-half">
                <label class="VV-label">COVERAGE RATE (%) *</label>
                <input class="VV-input" v-model="policyTabs[activePolicyTab].coverageRate" type="number" min="0" max="100" step="0.01" required placeholder="Enter coverage rate" />
                <small class="VV-desc">Range: 0-100, step: 0.01</small>
                </div>
              <div class="VV-form-group VV-half">
                <label class="VV-label">APPLICABILITY *</label>
                <input class="VV-input" v-model="policyTabs[activePolicyTab].applicability" type="text" required placeholder="Enter applicability" />
                <small class="VV-desc">Define the target audience, roles, or entities</small>
                </div>
                </div>
            <div class="VV-row">
              <div class="VV-form-group VV-half">
                <label class="VV-label">POLICY TYPE *</label>
                <div class="policy-type-multi-select" @click.stop>
                  <div class="policy-type-dropdown">
                    <div   
                      class="selected-policy-type" 
                      :class="{ active: policyTabs[activePolicyTab].showPolicyTypeDropdown }"
                      @click="togglePolicyTypeDropdown(activePolicyTab)"
                    >
                      <div class="policy-type-content">
                        <span v-if="policyTabs[activePolicyTab].type" class="policy-type-value">
                          {{ policyTabs[activePolicyTab].type }}
                        </span>
                        <span v-else class="placeholder">
                          Search or enter new policy type
                        </span>
                      </div>
                      <i class="fas fa-chevron-down dropdown-arrow"></i>
                    </div>
                    <div v-if="policyTabs[activePolicyTab].showPolicyTypeDropdown" class="policy-type-options">
                      <!-- Search Input -->
                      <div class="search-input-container">
                        <input
                          v-model="policyTabs[activePolicyTab].policyTypeSearch"
                          type="text"
                          placeholder="Search or type new policy type..."
                          class="search-input"
                          @input="filterPolicyTypes()"
                          @keyup.enter="createNewPolicyType(activePolicyTab)"
                        />
                      </div>
                      <!-- Existing Options -->
                      <div 
                        v-for="type in getFilteredPolicyTypes(activePolicyTab)" 
                        :key="type" 
                        class="policy-type-option"
                        @click="selectPolicyType(activePolicyTab, type)"
                      >
                        <span class="policy-type-label">{{ type }}</span>
                      </div>
                      <!-- Create New Option -->
                      <div 
                        v-if="policyTabs[activePolicyTab].policyTypeSearch && !getFilteredPolicyTypes(activePolicyTab).includes(policyTabs[activePolicyTab].policyTypeSearch)"
                        class="policy-type-option create-new-option"
                        @click="createNewPolicyType(activePolicyTab)"
                      >
                        <i class="fas fa-plus"></i>
                        <span class="policy-type-label">Create "{{ policyTabs[activePolicyTab].policyTypeSearch }}"</span>
                      </div>
                    </div>
                  </div>
                </div>
                <small class="VV-desc">Select from list or type new policy type</small>
              </div>
              <div class="VV-form-group VV-half">
                <label class="VV-label">POLICY CATEGORY *</label>
                <div class="policy-category-multi-select" @click.stop>
                  <div class="policy-category-dropdown">
                    <div   
                      class="selected-policy-category" 
                      :class="{ active: policyTabs[activePolicyTab].showPolicyCategoryDropdown }"
                      @click="togglePolicyCategoryDropdown(activePolicyTab)"
                    >
                      <div class="policy-category-content">
                        <span v-if="policyTabs[activePolicyTab].category" class="policy-category-value">
                          {{ policyTabs[activePolicyTab].category }}
                        </span>
                        <span v-else class="placeholder">
                          Search or enter new policy category
                        </span>
                      </div>
                      <i class="fas fa-chevron-down dropdown-arrow"></i>
                    </div>
                    <div v-if="policyTabs[activePolicyTab].showPolicyCategoryDropdown" class="policy-category-options">
                      <!-- Search Input -->
                      <div class="search-input-container">
                        <input
                          v-model="policyTabs[activePolicyTab].policyCategorySearch"
                          type="text"
                          placeholder="Search or type new policy category..."
                          class="search-input"
                          @input="filterPolicyCategories()"
                          @keyup.enter="createNewPolicyCategory(activePolicyTab)"
                        />
                      </div>
                      <!-- Existing Options -->
                      <div 
                        v-for="category in getFilteredPolicyCategories(activePolicyTab)" 
                        :key="category" 
                        class="policy-category-option"
                        @click="selectPolicyCategory(activePolicyTab, category)"
                      >
                        <span class="policy-category-label">{{ category }}</span>
                      </div>
                      <!-- Create New Option -->
                      <div 
                        v-if="policyTabs[activePolicyTab].policyCategorySearch && !getFilteredPolicyCategories(activePolicyTab).includes(policyTabs[activePolicyTab].policyCategorySearch)"
                        class="policy-category-option create-new-option"
                        @click="createNewPolicyCategory(activePolicyTab)"
                      >
                        <i class="fas fa-plus"></i>
                        <span class="policy-category-label">Create "{{ policyTabs[activePolicyTab].policyCategorySearch }}"</span>
                      </div>
                    </div>
                  </div>
                </div>
                <small class="VV-desc">Select from list or type new policy category</small>
              </div>
            </div>
            <div class="VV-row">
              <div class="VV-form-group VV-half">
                <label class="VV-label">POLICY SUB CATEGORY *</label>
                <div class="policy-subcategory-multi-select" @click.stop>
                  <div class="policy-subcategory-dropdown">
                    <div   
                      class="selected-policy-subcategory" 
                      :class="{ active: policyTabs[activePolicyTab].showPolicySubCategoryDropdown }"
                      @click="togglePolicySubCategoryDropdown(activePolicyTab)"
                    >
                      <div class="policy-subcategory-content">
                        <span v-if="policyTabs[activePolicyTab].subCategory" class="policy-subcategory-value">
                          {{ policyTabs[activePolicyTab].subCategory }}
                        </span>
                        <span v-else class="placeholder">
                          Search or enter new policy sub category
                        </span>
                      </div>
                      <i class="fas fa-chevron-down dropdown-arrow"></i>
                    </div>
                    <div v-if="policyTabs[activePolicyTab].showPolicySubCategoryDropdown" class="policy-subcategory-options">
                      <!-- Search Input -->
                      <div class="search-input-container">
                        <input
                          v-model="policyTabs[activePolicyTab].policySubCategorySearch"
                          type="text"
                          placeholder="Search or type new policy sub category..."
                          class="search-input"
                          @input="filterPolicySubCategories()"
                          @keyup.enter="createNewPolicySubCategory(activePolicyTab)"
                        />
                      </div>
                      <!-- Existing Options -->
                      <div 
                        v-for="subCategory in getFilteredPolicySubCategories(activePolicyTab)" 
                        :key="subCategory" 
                        class="policy-subcategory-option"
                        @click="selectPolicySubCategory(activePolicyTab, subCategory)"
                      >
                        <span class="policy-subcategory-label">{{ subCategory }}</span>
                      </div>
                      <!-- Create New Option -->
                      <div 
                        v-if="policyTabs[activePolicyTab].policySubCategorySearch && !getFilteredPolicySubCategories(activePolicyTab).includes(policyTabs[activePolicyTab].policySubCategorySearch)"
                        class="policy-subcategory-option create-new-option"
                        @click="createNewPolicySubCategory(activePolicyTab)"
                      >
                        <i class="fas fa-plus"></i>
                        <span class="policy-subcategory-label">Create "{{ policyTabs[activePolicyTab].policySubCategorySearch }}"</span>
                      </div>
                    </div>
                  </div>
                </div>
                <small class="VV-desc">Select from list or type new policy sub category</small>
              </div>
              <div class="VV-form-group VV-half">
                <label class="VV-label">APPLICABLE ENTITIES *</label>
                <div class="form-row">
                  <div class="form-group entities-group">
                    <div class="entities-multi-select" @click.stop>
                      <div class="entities-dropdown">
                        <div 
                          class="selected-entities" 
                          :class="{ 
                            'active': policyTabs[activePolicyTab]?.showEntitiesDropdown,
                            'error': error && error.includes('entities')
                          }"
                          @click="toggleEntitiesDropdown(activePolicyTab)"
                        >
                          <div class="entity-content">
                            <span v-if="loading" class="loading-text">
                              Loading entities...
                            </span>
                            <span v-else-if="isAllEntitiesSelected(activePolicyTab)" class="entity-tag all-tag">
                              All Locations
                            </span>
                            <span v-else-if="getSelectedEntitiesCount(activePolicyTab) === 0" class="placeholder">
                              Select entities...
                            </span>
                            <span v-else class="entity-count">
                              {{ getSelectedEntitiesCount(activePolicyTab) }} location(s) selected
                            </span>
                          </div>
                          <i class="fas fa-chevron-down dropdown-arrow"></i>
                        </div>
                        <div v-if="policyTabs[activePolicyTab]?.showEntitiesDropdown" class="entities-options">
                          <div v-if="loading" class="entities-loading">
                            Loading entities...
                          </div>
                          <div v-else-if="error" class="entities-error">
                            {{ error }}
                          </div>
                          <template v-else>
                            <div 
                              v-for="entity in entities" 
                              :key="entity.id" 
                              :class="['entity-option', { 'all-option': entity.id === 'all' }]"
                              @click="selectEntity(activePolicyTab, entity.id)"
                            >
                              <input 
                                type="checkbox" 
                                :checked="entity.id === 'all' ? isAllEntitiesSelected(activePolicyTab) : isEntitySelected(activePolicyTab, entity.id)"
                                @change="handleEntitySelection(activePolicyTab, entity.id, $event.target.checked)"
                                @click.stop
                              />
                              <span class="entity-label">{{ entity.label }}</span>
                            </div>
                          </template>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <small class="VV-desc">Select the locations/entities this policy applies to</small>
          </div>
        </div>
            <div class="VV-row">
              <div class="VV-form-group VV-half">
                <label class="VV-label">START DATE *</label>
                <input class="VV-input" v-model="policyTabs[activePolicyTab].startDate" type="date" required />
                <small class="VV-desc">Date when this policy takes effect</small>
      </div>
              <div class="VV-form-group VV-half">
                <label class="VV-label">END DATE *</label>
                <input class="VV-input" v-model="policyTabs[activePolicyTab].endDate" type="date" required />
                <small class="VV-desc">Date when this policy expires or requires review/renewal</small>
        </div>
            </div>
            <div class="VV-row">
              <div class="VV-form-group VV-half">
                <label class="VV-label">CREATED BY *</label>
                <input class="VV-input" :value="currentUser.UserName || loggedInUsername" type="text" disabled />
                <small class="VV-desc">Automatically set to logged in user</small>
              </div>
              <div class="VV-form-group VV-half">
                <label class="VV-label">REVIEWER *</label>
                <select 
                  class="VV-input" 
                  v-model="policyTabs[activePolicyTab].reviewer" 
                  required
                >
                  <option value="">Select Reviewer</option>
                  <option v-for="user in users" :key="user.id" :value="user.id">{{ user.name }}</option>
                </select>
                <small class="VV-desc">Select who will review this policy</small>
        </div>
            </div>
            <div class="VV-form-group">
              <label class="VV-label">UPLOAD DOCUMENT</label>
              <input class="VV-input" type="file" @change="e => handlePolicyFileUpload(e, activePolicyTab)" />
              <small class="VV-desc">Upload supporting documentation (optional)</small>
            </div>
          </form>
              </div>
            </div>
      <div v-if="policyTabs.length && policyTabs[activePolicyTab]" class="VV-subpolicy-tabs-container">
        <div class="VV-subpolicy-tabs-row">
          <div class="VV-subpolicy-tabs">
            <button v-for="(subTab, subIdx) in policyTabs[activePolicyTab].subPolicies" :key="subTab.id" :class="['VV-subpolicy-tab', { 'VV-subpolicy-tab-active': subIdx === policyTabs[activePolicyTab].activeSubPolicyTab, 'excluded': subTab.exclude }]" @click="policyTabs[activePolicyTab].activeSubPolicyTab = subIdx">
              Subpolicy {{ subIdx + 1 }}
            </button>
            <button class="VV-add-subpolicy-tab" @click="addSubPolicyTab(activePolicyTab)">+ Add Sub Policy</button>
          </div>
        </div>
        <div v-if="policyTabs[activePolicyTab].subPolicies && policyTabs[activePolicyTab].subPolicies.length" class="VV-subpolicy-form-container">
          <button 
            class="VV-exclude-subpolicy-btn" 
            @click="excludeSubPolicyTab(activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
            :class="{ 'excluded': policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].exclude }"
          >
            {{ policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].exclude ? 'Include' : 'Exclude' }}
          </button>
          <div v-if="policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].exclude" class="TT-excluded-message">
            This subpolicy has been excluded and will not be included in the submission.
          </div>
          <form>
            <div class="VV-form-group">
              <label class="VV-label">SUB POLICY NAME *</label>
              <input class="VV-input" v-model="policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].name" type="text" required placeholder="Enter sub policy name" @input="handleSubPolicyNameChange(activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab, $event.target.value)" />
              <small class="VV-desc">Use a clear name that describes this sub-policy's specific focus</small>
      </div>
            <div class="VV-form-group">
              <label class="VV-label">IDENTIFIER * 
                <span v-if="isInternalFramework()" class="auto-generated-label">(Auto-generated)</span>
                <span v-else class="manual-entry-label">(Manual entry)</span>
              </label>
              <input class="VV-input" v-model="policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].identifier" type="text" required placeholder="Enter identifier" :readonly="isInternalFramework()" />
              <small class="VV-desc">{{ isInternalFramework() ? 'Auto-generated based on parent policy identifier' : 'Enter a unique identifier for this sub-policy' }}</small>
        </div>
            <div class="VV-form-group">
              <label class="VV-label">CONTROL *</label>
              <textarea class="VV-textarea" v-model="policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].control" rows="3" required placeholder="Enter control"></textarea>
              <small class="VV-desc">Specify the control mechanisms, procedures, or safeguards to be implemented</small>
            </div>
            <div class="VV-form-group">
              <label class="VV-label">DESCRIPTION *</label>
              <textarea class="VV-textarea" v-model="policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].description" rows="3" required placeholder="Enter description"></textarea>
              <small class="VV-desc">Explain the intent, requirements, or significance of this sub-policy</small>
            </div>
          </form>
        </div>
      </div>
      </div>
      <div v-if="policyTabs.length && policyTabs[activePolicyTab]" class="VV-universal-submit-wrapper">
        <button class="VV-universal-submit-btn" @click.prevent="showVersionModal = true" :disabled="isPolicyCreatorReviewerSame">Submit</button>
      </div>
    </div>
    <!-- Add submit button for policy tab -->
  </template>
  
  <script>
import './VV.css'
import CustomDropdown from '../CustomDropdown.vue'
import axios from 'axios'
import { PopupService } from '@/modules/popup'  // Fix the import path

import {  API_BASE_URL, API_ENDPOINTS, axiosInstance } from '../../config/api.js'
const API_BASE_URL_FULL = `${API_BASE_URL}/api`

  export default {
name: 'VV',
  components: {
    CustomDropdown
  },
  data() {
    return {
      selectedTab: 'framework',
      selectedFramework: '',
      selectedPolicy: '',
      frameworkFormLoaded: false,
      frameworks: [],
      policies: [], // This will store policies for the dropdown
      policyTypes: [],
      policyCategories: [],
      policySubCategories: [],
      policyData: [], // Store all policy category data
      users: [], // Add users array
      entities: [], // Initialize as empty array
      departments: [], // Store all departments
      loggedInUsername: localStorage.getItem('username') || '', // Use username instead of user_name
      currentUser: {
        UserId: null,
        UserName: localStorage.getItem('username') || '',
        Role: null
      },
      frameworkForm: {
        name: '',
        description: '',
        identifier: '',
        category: '',
        internalExternal: '',
        file: null,
        startDate: '',
        endDate: '',
        createdByName: localStorage.getItem('username') || '', // Use username instead of user_name
        reviewer: ''
      },
      policyTabs: [],
      activePolicyTab: 0,
      loading: false,
      error: null,
      showVersionModal: false,
      selectedVersionType: 'minor', // Default version type
      existingFrameworkIdentifiers: [], // Add this to track existing identifiers
      previousFrameworkData: null, // Store previous framework data for comparison
      previousPolicyData: null, // Store previous policy data for comparison
      previousSubpolicyData: [] // Store previous subpolicy data for comparison
    }
  },
  computed: {
    // Check if creator and reviewer are the same person for framework
    isFrameworkCreatorReviewerSame() {
      if (!this.frameworkForm.reviewer || !this.currentUser.UserName) return false;
      const creatorUser = this.users.find(u => u.name === this.currentUser.UserName);
      const reviewerUser = this.users.find(u => u.id === this.frameworkForm.reviewer);
      return creatorUser && reviewerUser && creatorUser.id === reviewerUser.id;
    },
    // Check if creator and reviewer are the same person for current policy
    isPolicyCreatorReviewerSame() {
      // Check if we have the required data
      if (!this.policyTabs[this.activePolicyTab] || !this.currentUser.UserName) {
        console.log('DEBUG: Missing required data for policy warning check');
        return false;
      }
      
      const currentPolicy = this.policyTabs[this.activePolicyTab];
      
      // If no reviewer is selected, return false (no warning needed)
      if (!currentPolicy.reviewer) {
        console.log('DEBUG: No reviewer selected for policy');
        return false;
      }
      
      // Try to find creator user by name first, then by ID as fallback
      let creatorUser = this.users.find(u => u.name === this.currentUser.UserName);
      if (!creatorUser && this.currentUser.UserId) {
        creatorUser = this.users.find(u => u.id === this.currentUser.UserId);
      }
      const reviewerUser = this.users.find(u => u.id === currentPolicy.reviewer);
      
      console.log('DEBUG: Policy warning check - creatorUser:', creatorUser, 'reviewerUser:', reviewerUser, 'currentUser:', this.currentUser);
      
      const result = creatorUser && reviewerUser && creatorUser.id === reviewerUser.id;
      console.log('DEBUG: isPolicyCreatorReviewerSame result:', result);
      
      return result;
    }
  },
  watch: {
    async selectedFramework(newVal) {
      if (newVal && newVal !== '' && newVal !== '__new__') {
        // Save the selected framework to session
        try {
          const userId = this.currentUser.UserId || localStorage.getItem('user_id') || 'default_user'
          console.log('🔍 DEBUG: Saving framework to session in VV:', newVal)
          
          const response = await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
            frameworkId: newVal,
            userId: userId
          })
          
          if (response.data && response.data.success) {
            console.log('✅ DEBUG: Framework saved to session successfully in VV')
            console.log('🔑 DEBUG: Session key:', response.data.sessionKey)
          } else {
            console.error('❌ DEBUG: Failed to save framework to session in VV')
          }
        } catch (error) {
          console.error('❌ DEBUG: Error saving framework to session in VV:', error)
        }
      }
      
      if (this.selectedTab === 'framework') {
        this.handleFrameworkSelection(newVal)
      } else if (this.selectedTab === 'policy') {
        // In policy tab, just load policies for the dropdown
        this.loadPoliciesForFramework(newVal)
        // Clear selected policy when framework changes
        this.selectedPolicy = ''
        this.policyTabs = []
      }
    },
    selectedPolicy(newVal) {
      if (this.selectedTab === 'policy' && this.selectedFramework && newVal) {
        this.fetchPolicyDetails(newVal)
      }
    },
    selectedTab(newVal) {
      if (newVal === 'framework') {
        this.selectedPolicy = ''
        this.fetchFrameworks()
        if (this.selectedFramework) {
          this.handleFrameworkSelection(this.selectedFramework)
        }
      } else if (newVal === 'policy') {
        this.selectedPolicy = ''
        this.policyTabs = []
        this.fetchFrameworks()
        // Ensure policies are loaded for the selected framework in policy tab
        if (this.selectedFramework) {
          this.loadPoliciesForFramework(this.selectedFramework)
        }
      }
    },
    // Add watchers for auto-generating identifiers
    'frameworkForm.name': function(newVal) {
      if (newVal) {
        this.autoGenerateFrameworkIdentifier(newVal);
      }
    }
  },
  async created() {
    try {
      console.log('=== Component created - starting initialization')
      
      // Initialize frameworkForm.createdByName with loggedInUsername
      this.frameworkForm.createdByName = this.loggedInUsername;
      
      await Promise.all([
        this.fetchCurrentUser(), // Fetch current user first
        this.fetchFrameworks(),
        this.fetchPolicyData(),
        this.fetchEntities(),
        this.fetchUsers(),
        this.fetchDepartments(),
        this.fetchExistingFrameworkIdentifiers() // Add this to fetch existing identifiers
      ])
      
      console.log('=== Component initialization completed')
      console.log('Frameworks loaded:', this.frameworks.length)
      console.log('Users loaded:', this.users.length)
      console.log('Current user:', this.currentUser)
      
    } catch (error) {
      console.error('Error in component creation:', error)
      this.error = 'Failed to initialize component'
    }
  },
  methods: {
    async fetchCurrentUser() {
      try {
        console.log('=== DEBUG fetchCurrentUser ===');
      const response = await axios.get(`${API_BASE_URL_FULL}/user-role/`)
      console.log('API response:', response.data);
      
      if (response.data.success) {
        this.currentUser = {
          UserId: response.data.user_id,
          UserName: response.data.username || response.data.user_name || localStorage.getItem('username') || '',
          Role: response.data.role
        }
        // Update loggedInUsername and frameworkForm.createdByName with current user name
        this.loggedInUsername = this.currentUser.UserName
        this.frameworkForm.createdByName = this.currentUser.UserName
        
        console.log('Current user loaded:', this.currentUser)
        console.log('loggedInUsername set to:', this.loggedInUsername)
        console.log('frameworkForm.createdByName set to:', this.frameworkForm.createdByName)
      }
    } catch (err) {
      console.error('Error fetching current user:', err)
      // Fallback to localStorage if API fails
      const storedUsername = localStorage.getItem('username')
      console.log('Fallback - storedUsername from localStorage:', storedUsername)
      if (storedUsername) {
        this.currentUser.UserName = storedUsername
        this.loggedInUsername = storedUsername
        this.frameworkForm.createdByName = storedUsername
        console.log('Fallback values set:', {
          currentUser: this.currentUser,
          loggedInUsername: this.loggedInUsername,
          createdByName: this.frameworkForm.createdByName
        })
      }
    }
  },
  // Add new identifier generation functions
  async fetchExistingFrameworkIdentifiers() {
    try {
      const response = await axios.get(`${API_BASE_URL_FULL}/frameworks/`, {
        params: { include_all_for_identifiers: 'true' }
      });
      this.existingFrameworkIdentifiers = response.data
        .map(fw => fw.Identifier)
        .filter(id => id);
      console.log('Fetched existing framework identifiers:', this.existingFrameworkIdentifiers);
    } catch (err) {
      console.error('Error fetching existing framework identifiers:', err);
    }
  },

  generateFrameworkIdentifier(frameworkName) {
    if (!frameworkName || frameworkName.length < 4) return '';
    
    const prefix = frameworkName.substring(0, 4).toUpperCase();
    let counter = 1;
    let identifier = `${prefix}${counter}`;
    
    // Check against existing identifiers
    while (this.existingFrameworkIdentifiers.includes(identifier)) {
      counter++;
      identifier = `${prefix}${counter}`;
    }
    
    return identifier;
  },

  autoGenerateFrameworkIdentifier(frameworkName) {
    if (frameworkName) {
      const generatedId = this.generateFrameworkIdentifier(frameworkName);
      this.frameworkForm.identifier = generatedId;
    }
  },

  generatePolicyIdentifier(policyName) {
    if (!policyName) return '';
    
    // Split by spaces and take first letter of each word
    const words = policyName.split(' ').filter(word => word.length > 0);
    return words.map(word => word.charAt(0).toUpperCase()).join('');
  },

  generateSubPolicyIdentifier(policyIdentifier, subPolicyIndex) {
    if (!policyIdentifier) return '';
    return `${policyIdentifier}-${subPolicyIndex + 1}`;
  },

  // Helper function to check if current context is for internal framework
  isInternalFramework() {
    return this.frameworkForm.internalExternal === 'Internal';
  },

  handlePolicyNameChange(idx, value) {
    // Update the policy name
    this.policyTabs[idx].name = value;
    
    // Auto-generate identifier when name changes (only for internal frameworks)
    if (value && this.isInternalFramework()) {
      const generatedId = this.generatePolicyIdentifier(value);
      this.policyTabs[idx].identifier = generatedId;
      
      // Also update all subpolicy identifiers
      if (this.policyTabs[idx].subPolicies) {
        this.policyTabs[idx].subPolicies.forEach((subpolicy, subIdx) => {
          if (subpolicy.name) {
            subpolicy.identifier = this.generateSubPolicyIdentifier(generatedId, subIdx);
          }
        });
      }
    }
  },

  handleSubPolicyNameChange(policyIdx, subIdx, value) {
    // Update the subpolicy name
    this.policyTabs[policyIdx].subPolicies[subIdx].name = value;
    
    // Auto-generate identifier when name changes (only for internal frameworks)
    if (value && this.policyTabs[policyIdx].identifier && this.isInternalFramework()) {
      const policyIdentifier = this.policyTabs[policyIdx].identifier;
      this.policyTabs[policyIdx].subPolicies[subIdx].identifier = 
        this.generateSubPolicyIdentifier(policyIdentifier, subIdx);
    }
  },
  
  selectTab(tab) {
    this.selectedTab = tab
  },
  handleFileUpload(e) {
    this.frameworkForm.file = e.target.files[0]
      },
    
    // Method to refresh frameworks if they disappear
    async refreshFrameworks() {
      console.log('=== Refreshing frameworks...')
      await this.fetchFrameworks()
      
      // If we had a selected framework but it's no longer in the list, clear it
      if (this.selectedFramework && !this.frameworks.find(fw => String(fw.id) === String(this.selectedFramework))) {
        console.log('Selected framework no longer exists, clearing selection')
        this.selectedFramework = ''
        this.selectedPolicy = ''
        this.policyTabs = []
        this.policies = []
      }
    },
    
    // Add the missing addSubPolicyTab method
    addSubPolicyTab(policyIdx) {
    const currentUsername = this.currentUser.UserName || this.loggedInUsername || '';
    
    this.policyTabs[policyIdx].subPolicies.push({
      id: `new-subpolicy-${Date.now()}`, // Add 'new-' prefix to identify new subpolicies
      name: '',
      identifier: '',
      control: '',
      description: '',
      createdByName: currentUsername, // Use current username
      exclude: false
    })
    this.policyTabs[policyIdx].activeSubPolicyTab = this.policyTabs[policyIdx].subPolicies.length - 1
  },
  // Add method to handle policy tab addition
  addPolicyTab() {
    const newPolicyId = `new-policy-${Date.now()}`;
    console.log('Creating new policy with ID:', newPolicyId);
    
    const reviewer = this.selectedTab === 'framework' ? this.frameworkForm.reviewer : '';
    const currentUsername = this.currentUser.UserName || this.loggedInUsername || '';
    
    this.policyTabs.push({
      id: newPolicyId,
      name: '',
      identifier: '',
      description: '',
      scope: '',
      department: '',
      objective: '',
      coverageRate: '',
      applicability: '',
      type: '',
      category: '',
      subCategory: '',
      entities: [],
      startDate: '',
      endDate: '',
      file: null,
      createdByName: currentUsername, // Use current username
      reviewer: reviewer,
      exclude: false,
      subPolicies: [
        {
          id: `new-subpolicy-${Date.now()}`,
          name: '',
          identifier: '',
          control: '',
          description: '',
          createdByName: currentUsername, // Use current username
          exclude: false
        }
      ],
      activeSubPolicyTab: 0
    });
    this.activePolicyTab = this.policyTabs.length - 1;
  },

  async fetchFrameworks() {
    try {
      this.loading = true
      this.error = null // Clear any previous errors
      
      console.log('=== Fetching frameworks...')
      const response = await axios.get(`${API_BASE_URL_FULL}/frameworks/`)
      console.log('Raw framework response:', response.data)
      
      // Map frameworks
      this.frameworks = response.data.map(fw => ({ 
        id: fw.FrameworkId, 
        name: fw.FrameworkName,
        description: fw.FrameworkDescription,
        category: fw.Category,
        internalExternal: fw.InternalExternal,
        startDate: fw.StartDate,
        endDate: fw.EndDate,
        status: fw.Status
      }))

      console.log('Mapped frameworks:', this.frameworks)
      console.log('Frameworks count:', this.frameworks.length)

      if (this.frameworks.length === 0) {
        console.log('No frameworks found')
        PopupService.info('No frameworks found', 'No Data');
      } else {
        console.log('Frameworks loaded successfully')
      }

      // Check for selected framework from session after loading frameworks
      await this.checkSelectedFrameworkFromSession()

    } catch (error) {
      console.error('Error fetching frameworks:', error)
      this.error = 'Failed to fetch frameworks'
      this.frameworks = [] // Clear frameworks on error
      PopupService.error('Failed to fetch frameworks', 'Error')
    } finally {
      this.loading = false
    }
  },

  // Check for selected framework from session and set it as default
  async checkSelectedFrameworkFromSession() {
    try {
      console.log('🔍 DEBUG: Checking for selected framework from session in VV...')
      const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
      console.log('📊 DEBUG: Selected framework response:', response.data)
      
      if (response.data && response.data.success) {
        // Check if a framework is selected (not null)
        if (response.data.frameworkId) {
        const sessionFrameworkId = response.data.frameworkId
        console.log('✅ DEBUG: Found selected framework in session:', sessionFrameworkId)
        
        // Check if this framework exists in our loaded frameworks
        const frameworkExists = this.frameworks.find(f => String(f.id) === String(sessionFrameworkId))
        
        if (frameworkExists) {
          this.selectedFramework = String(sessionFrameworkId)
          console.log('✅ DEBUG: Set selected framework from session:', this.selectedFramework)
          
          // If in framework tab, load framework details
          if (this.selectedTab === 'framework') {
            await this.handleFrameworkSelection(sessionFrameworkId)
          } else if (this.selectedTab === 'policy') {
            // If in policy tab, load policies for this framework
            await this.loadPoliciesForFramework(sessionFrameworkId)
          }
        } else {
          console.log('⚠️ DEBUG: Framework from session not found in loaded frameworks')
          }
        } else {
          // "All Frameworks" is selected (frameworkId is null)
          console.log('ℹ️ DEBUG: No framework selected in session (All Frameworks selected)')
          console.log('🌐 DEBUG: Clearing framework selection to show all frameworks')
          this.selectedFramework = ''
          this.policies = []
        }
      } else {
        console.log('ℹ️ DEBUG: No framework found in session')
        this.selectedFramework = ''
      }
    } catch (error) {
      console.error('❌ DEBUG: Error checking selected framework from session:', error)
      // Clear selection on error
      this.selectedFramework = ''
    }
  },

  // Add new methods for policy type/category handling
  async fetchPolicyData() {
    try {
      const response = await axios.get(`${API_BASE_URL_FULL}/policy-categories/`)
      this.policyData = response.data
      
      // Extract unique policy types
      this.policyTypes = [...new Set(this.policyData.map(item => item.PolicyType))]
      console.log('Fetched policy types:', this.policyTypes)
    } catch (error) {
      console.error('Error fetching policy data:', error)
      this.error = 'Failed to fetch policy data'
      PopupService.error('Failed to fetch policy data', 'Error')
    }
  },

  handlePolicyTypeChange(idx, value) {
    console.log('Policy type changed:', value)
    const policy = this.policyTabs[idx]
    policy.type = value
    policy.category = '' // Clear category when type changes
    policy.subCategory = '' // Clear subcategory when type changes
    
    // Update available categories for this type
    this.updatePolicyCategoriesByType(value)
  },

  handlePolicyCategoryChange(idx, value) {
    console.log('Policy category changed:', value)
    const policy = this.policyTabs[idx]
    policy.category = value
    policy.subCategory = '' // Clear subcategory when category changes
    
    // Update available subcategories for this type and category
    this.updateSubCategoriesByCategory(policy.type, value)
  },

  handlePolicySubCategoryChange(idx, value) {
    console.log('Policy subcategory changed:', value)
    this.policyTabs[idx].subCategory = value
  },

  updatePolicyCategoriesByType(policyType) {
    console.log('Updating categories for type:', policyType)
    if (!policyType || !this.policyData) {
      this.policyCategories = []
      this.policySubCategories = []
      return
    }

    // Filter categories based on selected type
    const filteredData = this.policyData.filter(item => item.PolicyType === policyType)
    console.log('Filtered data:', filteredData)

    const categories = [...new Set(filteredData.map(item => item.PolicyCategory))]
    console.log('Available categories for type:', categories)
    this.policyCategories = categories

    // Reset category and subcategory in the active policy tab
    if (this.policyTabs[this.activePolicyTab]) {
      this.policyTabs[this.activePolicyTab].category = ''
      this.policyTabs[this.activePolicyTab].subCategory = ''
    }
    this.policySubCategories = []
  },

  updateSubCategoriesByCategory(policyType, policyCategory) {
    console.log('Updating subcategories for type:', policyType, 'and category:', policyCategory)
    if (!policyType || !policyCategory || !this.policyData) {
      this.policySubCategories = []
      return
    }

    // Filter subcategories based on selected type and category
    const filteredData = this.policyData.filter(item => 
      item.PolicyType === policyType && 
      item.PolicyCategory === policyCategory
    )
    console.log('Filtered data:', filteredData)

    const subcategories = [...new Set(filteredData.map(item => item.PolicySubCategory))]
    console.log('Available subcategories:', subcategories)
    this.policySubCategories = subcategories

    // Reset subcategory in the active policy tab
    if (this.policyTabs[this.activePolicyTab]) {
      this.policyTabs[this.activePolicyTab].subCategory = ''
    }
  },

    // Policy Type Dropdown Methods
    togglePolicyTypeDropdown(idx) {
      // Close other dropdowns first
      this.policyTabs.forEach((tab, i) => {
        if (i !== idx) {
          tab.showPolicyTypeDropdown = false;
          tab.showPolicyCategoryDropdown = false;
          tab.showPolicySubCategoryDropdown = false;
        }
      });
      
      this.policyTabs[idx].showPolicyTypeDropdown = !this.policyTabs[idx].showPolicyTypeDropdown;
    },

    filterPolicyTypes() {
      // This function is called on input to filter policy types
      // The filtering is handled in getFilteredPolicyTypes
    },

    getFilteredPolicyTypes(idx) {
      const searchQuery = this.policyTabs[idx].policyTypeSearch || '';
      if (!searchQuery) return this.policyTypes;
      
      return this.policyTypes.filter(type => 
        type.toLowerCase().includes(searchQuery.toLowerCase())
      );
    },

    selectPolicyType(idx, type) {
      this.policyTabs[idx].type = type;
      this.policyTabs[idx].showPolicyTypeDropdown = false;
      this.policyTabs[idx].policyTypeSearch = '';
      
      // Clear category and subcategory when type changes
      this.policyTabs[idx].category = '';
      this.policyTabs[idx].subCategory = '';
      
      // Update available categories for this type
      this.updatePolicyCategoriesByType(type);
    },

    async createNewPolicyType(idx) {
      const newType = this.policyTabs[idx].policyTypeSearch?.trim();
      if (!newType) return;
      
      try {
        // Add to local array first for immediate UI update
        if (!this.policyTypes.includes(newType)) {
          this.policyTypes.push(newType);
        }
        
        // Select the new type
        this.selectPolicyType(idx, newType);
        
        // Clear search
        this.policyTabs[idx].policyTypeSearch = '';
        
        // Show success message
        if (this.$toast) {
          this.$toast.success(`Policy type "${newType}" added successfully!`);
        }
      } catch (err) {
        console.error('Error creating policy type:', err);
        if (this.$toast) {
          this.$toast.error('Failed to create policy type. Please try again.');
        }
      }
    },

    // Policy Category Dropdown Methods
    togglePolicyCategoryDropdown(idx) {
      // Close other dropdowns first
      this.policyTabs.forEach((tab, i) => {
        if (i !== idx) {
          tab.showPolicyTypeDropdown = false;
          tab.showPolicyCategoryDropdown = false;
          tab.showPolicySubCategoryDropdown = false;
        }
      });
      
      this.policyTabs[idx].showPolicyCategoryDropdown = !this.policyTabs[idx].showPolicyCategoryDropdown;
    },

    filterPolicyCategories() {
      // This function is called on input to filter policy categories
      // The filtering is handled in getFilteredPolicyCategories
    },

    getFilteredPolicyCategories(idx) {
      const searchQuery = this.policyTabs[idx].policyCategorySearch || '';
      const policyType = this.policyTabs[idx].type;
      
      if (!policyType) return [];
      
      const categories = this.getCategoriesForType(policyType);
      
      if (!searchQuery) return categories;
      
      return categories.filter(category => 
        category.toLowerCase().includes(searchQuery.toLowerCase())
      );
    },

    selectPolicyCategory(idx, category) {
      this.policyTabs[idx].category = category;
      this.policyTabs[idx].showPolicyCategoryDropdown = false;
      this.policyTabs[idx].policyCategorySearch = '';
      
      // Clear subcategory when category changes
      this.policyTabs[idx].subCategory = '';
      
      // Update available subcategories for this type and category
      this.updateSubCategoriesByCategory(this.policyTabs[idx].type, category);
    },

    async createNewPolicyCategory(idx) {
      const newCategory = this.policyTabs[idx].policyCategorySearch?.trim();
      const policyType = this.policyTabs[idx].type;
      
      if (!newCategory || !policyType) {
        if (this.$toast) {
          this.$toast.error('Please select a policy type first.');
        }
        return;
      }
      
      try {
        // Add to local array first for immediate UI update
        const categories = this.getCategoriesForType(policyType);
        if (!categories.includes(newCategory)) {
          // Add to policyCategories array
          this.policyCategories.push(newCategory);
        }
        
        // Select the new category
        this.selectPolicyCategory(idx, newCategory);
        
        // Clear search
        this.policyTabs[idx].policyCategorySearch = '';
        
        // Show success message
        if (this.$toast) {
          this.$toast.success(`Policy category "${newCategory}" added successfully!`);
        }
      } catch (err) {
        console.error('Error creating policy category:', err);
        if (this.$toast) {
          this.$toast.error('Failed to create policy category. Please try again.');
        }
      }
    },

    // Policy Subcategory Dropdown Methods
    togglePolicySubCategoryDropdown(idx) {
      // Close other dropdowns first
      this.policyTabs.forEach((tab, i) => {
        if (i !== idx) {
          tab.showPolicyTypeDropdown = false;
          tab.showPolicyCategoryDropdown = false;
          tab.showPolicySubCategoryDropdown = false;
        }
      });
      
      this.policyTabs[idx].showPolicySubCategoryDropdown = !this.policyTabs[idx].showPolicySubCategoryDropdown;
    },

    filterPolicySubCategories() {
      // This function is called on input to filter policy subcategories
      // The filtering is handled in getFilteredPolicySubCategories
    },

    getFilteredPolicySubCategories(idx) {
      const searchQuery = this.policyTabs[idx].policySubCategorySearch || '';
      const policyType = this.policyTabs[idx].type;
      const policyCategory = this.policyTabs[idx].category;
      
      if (!policyType || !policyCategory) return [];
      
      const subCategories = this.getSubCategoriesForCategory(policyType, policyCategory);
      
      if (!searchQuery) return subCategories;
      
      return subCategories.filter(subCategory => 
        subCategory.toLowerCase().includes(searchQuery.toLowerCase())
      );
    },

    selectPolicySubCategory(idx, subCategory) {
      this.policyTabs[idx].subCategory = subCategory;
      this.policyTabs[idx].showPolicySubCategoryDropdown = false;
      this.policyTabs[idx].policySubCategorySearch = '';
    },

    async createNewPolicySubCategory(idx) {
      const newSubCategory = this.policyTabs[idx].policySubCategorySearch?.trim();
      const policyType = this.policyTabs[idx].type;
      const policyCategory = this.policyTabs[idx].category;
      
      if (!newSubCategory || !policyType || !policyCategory) {
        if (this.$toast) {
          this.$toast.error('Please select a policy type and category first.');
        }
        return;
      }
      
      try {
        // Add to local array first for immediate UI update
        const subCategories = this.getSubCategoriesForCategory(policyType, policyCategory);
        if (!subCategories.includes(newSubCategory)) {
          // Add to policySubCategories array
          this.policySubCategories.push(newSubCategory);
          
          // Save to database immediately if we have a selected framework
          if (this.selectedFramework) {
            console.log('🔍 DEBUG: Saving new policy subcategory combination to database immediately');
            console.log('🔍 DEBUG: Data:', { policyType, policyCategory, newSubCategory, framework: this.selectedFramework });
            try {
              const response = await axios.post(API_ENDPOINTS.POLICY_CATEGORIES_SAVE, {
                PolicyType: policyType,
                PolicyCategory: policyCategory,
                PolicySubCategory: newSubCategory,
                frameworkId: this.selectedFramework
              });
              console.log('✅ DEBUG: Policy category combination saved to database:', response.data);
              
              // Refresh policy categories after saving
              await this.fetchPolicyCategories();
            } catch (apiError) {
              console.error('❌ DEBUG: Failed to save policy category combination to database:', apiError);
              console.error('❌ DEBUG: Error response:', apiError.response?.data);
              console.error('❌ DEBUG: Error status:', apiError.response?.status);
            }
          } else {
            console.warn('⚠️ DEBUG: No framework selected, policy category will not be saved to database');
          }
        }
        
        // Select the new subcategory
        this.selectPolicySubCategory(idx, newSubCategory);
        
        // Clear search
        this.policyTabs[idx].policySubCategorySearch = '';
        
        // Show success message
        if (this.$toast) {
          this.$toast.success(`Policy subcategory "${newSubCategory}" added successfully!`);
        }
      } catch (err) {
        console.error('Error creating policy subcategory:', err);
        if (this.$toast) {
          this.$toast.error('Failed to create policy subcategory. Please try again.');
        }
      }
    },

    getCategoriesForType(policyType) {
      if (!policyType || !this.policyData) return [];
      const categories = this.policyData
        .filter(item => item.PolicyType === policyType)
        .map(item => item.PolicyCategory);
      return [...new Set(categories)];
    },

    getSubCategoriesForCategory(policyType, policyCategory) {
      if (!policyType || !policyCategory || !this.policyData) return [];
      const subCategories = this.policyData
        .filter(item => item.PolicyType === policyType && item.PolicyCategory === policyCategory)
        .map(item => item.PolicySubCategory);
      return [...new Set(subCategories)];
    },

    // Add entity handling methods
    async fetchEntities() {
      try {
        this.loading = true
        const response = await axios.get(`${API_BASE_URL_FULL}/entities/`)
        console.log('Raw entities response:', response.data)
        
        if (response.data.entities) {
          // Map entities directly from the backend response
          this.entities = response.data.entities.map(entity => ({
            id: entity.id,
            label: entity.label
          }))
          console.log('Mapped entities:', this.entities)
        } else {
          throw new Error('Invalid response format')
        }
      } catch (error) {
        console.error('Error fetching entities:', error)
        this.error = 'Failed to fetch entities'
      } finally {
        this.loading = false
      }
    },

    handleEntitySelection(idx, entityId, isChecked) {
      if (idx < 0 || !this.policyTabs[idx]) return
      
      console.log('handleEntitySelection:', { idx, entityId, isChecked })
      
      // Initialize entities if undefined
      if (!this.policyTabs[idx].entities) {
        this.policyTabs[idx].entities = []
      }
      
      if (entityId === 'all') {
        // When "All Locations" is selected, set entities to "all" string
        this.policyTabs[idx].entities = isChecked ? "all" : []
      } else {
        // Ensure we're working with an array
        let currentEntities = this.policyTabs[idx].entities === "all" ? [] 
          : Array.isArray(this.policyTabs[idx].entities) ? this.policyTabs[idx].entities 
          : []
        
        const numericId = Number(entityId)
        
        if (isChecked) {
          if (!currentEntities.includes(numericId)) {
            currentEntities.push(numericId)
          }
        } else {
          currentEntities = currentEntities.filter(id => id !== numericId)
        }
        
        // Store as array of numeric IDs
        this.policyTabs[idx].entities = currentEntities
      }
      
      console.log('Updated entities:', this.policyTabs[idx].entities)
    },

    selectEntity(idx, entityId) {
      if (idx < 0 || !this.policyTabs[idx]) return
      
      const isSelected = entityId === 'all' 
        ? this.isAllEntitiesSelected(idx)
        : this.isEntitySelected(idx, entityId)
      
      this.handleEntitySelection(idx, entityId, !isSelected)
    },

    isEntitySelected(idx, entityId) {
      const policy = this.policyTabs[idx]
      if (!policy || !policy.entities) return false
      
      if (policy.entities === "all") {
        return entityId === 'all'
      }
      
      return Array.isArray(policy.entities) && policy.entities.includes(Number(entityId))
    },

    isAllEntitiesSelected(idx) {
      const policy = this.policyTabs[idx]
      return policy && policy.entities === "all"
    },

    getSelectedEntitiesCount(idx) {
      const policy = this.policyTabs[idx]
      if (!policy || !policy.entities) return 0
      
      if (policy.entities === "all") {
        return this.entities.length - 1 // Subtract 1 for the "All" option
      }
      
      return Array.isArray(policy.entities) ? policy.entities.length : 0
    },

    toggleEntitiesDropdown(idx) {
      if (idx < 0 || !this.policyTabs[idx]) return
      
      // Close all other dropdowns first
      this.policyTabs.forEach((policy, index) => {
        if (index !== idx) {
          policy.showEntitiesDropdown = false
        }
      })
      
      // Toggle current dropdown
      const currentPolicy = this.policyTabs[idx]
      currentPolicy.showEntitiesDropdown = !currentPolicy.showEntitiesDropdown
      
      // If opening the dropdown and no entities loaded yet, fetch them
      if (currentPolicy.showEntitiesDropdown && this.entities.length <= 1) {
        this.fetchEntities()
      }
    },

    closeAllEntityDropdowns() {
      this.policyTabs.forEach(policy => {
        policy.showEntitiesDropdown = false
      })
    },
    async handleFrameworkSelection(newVal) {
      if (!newVal) {
        this.resetForm()
        this.frameworkFormLoaded = false
        this.policies = [] // Clear policies when no framework is selected
        this.previousFrameworkData = null // Clear previous framework data
        return
      }

      try {
        this.loading = true
        this.frameworkFormLoaded = false
        this.error = null // Clear any previous errors
        
        console.log('=== Starting framework selection for ID:', newVal)
        
        // Fetch framework details first
        const frameworkResponse = await axios.get(`${API_BASE_URL_FULL}/frameworks/${newVal}/`)
        console.log('Raw framework details:', frameworkResponse.data)

        const framework = frameworkResponse.data
        
        // Store the previous framework data for version comparison
        this.previousFrameworkData = framework
        
        // Log reviewer data before assignment
        console.log('DEBUG: Framework reviewer data:', {
          reviewer: framework.Reviewer,
          reviewerName: framework.ReviewerName
        })
        
        // Get the reviewer name from the framework
        const frameworkReviewer = framework.ReviewerName || framework.Reviewer || ''
        
        // Get current username from localStorage
        const currentUsername = this.currentUser.UserName || this.loggedInUsername || ''
        
        this.frameworkForm = {
          name: framework.FrameworkName,
          description: framework.FrameworkDescription,
          identifier: framework.Identifier,
          category: framework.Category,
          internalExternal: framework.InternalExternal,
          file: null,
          startDate: framework.StartDate,
          endDate: framework.EndDate,
          createdByName: currentUsername, // Use current username instead of framework.CreatedByName
          reviewer: this.getUserIdByName(frameworkReviewer) // Convert user name to user ID for dropdown
        }
        
        // Log frameworkForm after assignment
        console.log('DEBUG: Framework form after assignment:', {
          reviewer: this.frameworkForm.reviewer
        })

        // Now fetch policies for this framework
        console.log('=== Fetching policies for framework:', newVal)
        const policiesResponse = await axios.get(`${API_BASE_URL_FULL}/frameworks/${newVal}/get-policies/`)
        console.log('Raw framework policies:', policiesResponse.data)

        // Filter for Approved and Active policies only
        const approvedActivePolicies = policiesResponse.data.filter(p => 
          p.Status === 'Approved' && p.ActiveInactive === 'Active'
        )
        
        console.log('Approved and active policies:', approvedActivePolicies)

        // Populate the policies array for the dropdown
        this.policies = approvedActivePolicies.map(p => ({
          id: p.PolicyId,
          name: p.PolicyName
        }))
        
        console.log('Policies array for dropdown:', this.policies)

        // Map policies for policy tabs with better error handling
        const policiesWithDetails = []
        
        for (const p of approvedActivePolicies) {
          try {
            console.log('=== Fetching subpolicies for policy:', p.PolicyId)
            const subpoliciesResponse = await axios.get(`${API_BASE_URL_FULL}/policies/${p.PolicyId}/get-subpolicies/`)
            console.log('Subpolicies for policy', p.PolicyId, ':', subpoliciesResponse.data)
            
            // In framework mode, use framework's reviewer for all policies and subpolicies
            const policyReviewer = this.selectedTab === 'framework' ? frameworkReviewer : (p.ReviewerName || p.Reviewer || '')
            
            const policyWithDetails = {
              id: p.PolicyId.toString(), // Ensure ID is a string
              name: p.PolicyName,
              description: p.PolicyDescription,
              status: p.Status,
              department: p.Department,
              scope: p.Scope,
              objective: p.Objective,
              identifier: p.Identifier,
              coverageRate: p.CoverageRate,
              applicability: p.Applicability,
              type: p.PolicyType,
              category: p.PolicyCategory,
              subCategory: p.PolicySubCategory,
              entities: p.Entities,
              startDate: p.StartDate,
              endDate: p.EndDate,
              file: null,
              createdByName: p.CreatedByName || framework.CreatedByName,
              reviewer: this.getUserIdByName(policyReviewer), // Convert user name to user ID for dropdown
              exclude: false, // Initialize exclude as false
              activeSubPolicyTab: 0,
              subPolicies: subpoliciesResponse.data.map(sp => ({
                id: sp.SubPolicyId.toString(), // Ensure ID is a string
                name: sp.SubPolicyName,
                identifier: sp.Identifier,
                control: sp.Control,
                description: sp.Description,
                status: sp.Status
              }))
            }
            
            policiesWithDetails.push(policyWithDetails)
            console.log('Added policy with details:', policyWithDetails.name)
            
          } catch (subpolicyError) {
            console.error('Error fetching subpolicies for policy', p.PolicyId, ':', subpolicyError)
            // Continue with other policies even if one fails
            const policyWithDetails = {
              id: p.PolicyId.toString(),
              name: p.PolicyName,
              description: p.PolicyDescription,
              status: p.Status,
              department: p.Department,
              scope: p.Scope,
              objective: p.Objective,
              identifier: p.Identifier,
              coverageRate: p.CoverageRate,
              applicability: p.Applicability,
              type: p.PolicyType,
              category: p.PolicyCategory,
              subCategory: p.PolicySubCategory,
              entities: p.Entities,
              startDate: p.StartDate,
              endDate: p.EndDate,
              file: null,
              createdByName: p.CreatedByName || framework.CreatedByName,
              reviewer: this.getUserIdByName(frameworkReviewer),
              exclude: false,
              activeSubPolicyTab: 0,
              subPolicies: [] // Empty array if subpolicies failed to load
            }
            policiesWithDetails.push(policyWithDetails)
          }
        }

        console.log('Final policies with details:', policiesWithDetails)

        if (policiesWithDetails.length === 0) {
          console.log('No policies found for framework')
          PopupService.info('No approved and active policies found for this framework', 'No Policies')
        }

        this.policyTabs = policiesWithDetails
        this.activePolicyTab = 0
        this.frameworkFormLoaded = true
        
        console.log('=== Framework selection completed successfully')
        console.log('Policy tabs set:', this.policyTabs.length, 'policies')
        console.log('Policies dropdown array:', this.policies.length, 'policies')

      } catch (error) {
        console.error('Error handling framework selection:', error)
        this.error = 'Failed to load framework details'
        this.policies = [] // Clear policies on error
        this.policyTabs = [] // Clear policy tabs on error
        this.frameworkFormLoaded = false
        PopupService.error('Failed to load framework details', 'Error')
      } finally {
        this.loading = false
      }
    },
    
    // Method to load policies for a specific framework (for policy tab)
    async loadPoliciesForFramework(frameworkId) {
      if (!frameworkId) return;
      
      try {
        console.log('=== Loading policies for framework in policy tab:', frameworkId);
        const response = await axios.get(`${API_BASE_URL_FULL}/frameworks/${frameworkId}/get-policies/`);
        console.log('Policies response for framework:', response.data);
        
        // Filter for Approved and Active policies only
        const approvedActivePolicies = response.data.filter(p => 
          p.Status === 'Approved' && p.ActiveInactive === 'Active'
        );
        
        // Populate the policies array for the dropdown
        this.policies = approvedActivePolicies.map(p => ({
          id: p.PolicyId,
          name: p.PolicyName
        }));
        
        console.log('Policies loaded for dropdown:', this.policies);
        
      } catch (error) {
        console.error('Error loading policies for framework:', error);
        this.policies = [];
        this.error = 'Failed to load policies for selected framework';
      }
    },
    
    // Helper method to convert user ID to user name
    getUserNameById(userId) {
      if (!userId || !this.users || this.users.length === 0) return '';
      const user = this.users.find(u => u.id === userId);
      return user ? user.name : '';
    },
    // Helper method to convert user name to user ID
    getUserIdByName(userName) {
      if (!userName || !this.users || this.users.length === 0) return '';
      const user = this.users.find(u => u.name === userName);
      return user ? user.id : '';
    },
    async submitFrameworkVersion() {
      try {
        this.loading = true;
        console.log('Submitting framework version with policies:', this.policyTabs);
        
        // Save any new departments and policy categories first
        await this.saveNewDepartments();
        await this.saveNewPolicyCategories();
        
        // Validate required fields
        if (!this.validateForm('framework')) {
          return;
        }

        // Format data for submission
        const versionData = {
          version_type: this.selectedVersionType,
          FrameworkName: this.frameworkForm.name,
          FrameworkDescription: this.frameworkForm.description,
          Category: this.frameworkForm.category,
          StartDate: this.frameworkForm.startDate,
          EndDate: this.frameworkForm.endDate,
          Identifier: this.frameworkForm.identifier,
          CreatedByName: this.frameworkForm.createdByName,
          ReviewerName: this.getUserNameById(this.frameworkForm.reviewer),
          InternalExternal: this.frameworkForm.internalExternal,
          policies: [],
          new_policies: []
        };

        // Process each policy tab
        this.policyTabs.forEach(policy => {
          // Skip excluded policies
          if (policy.exclude) {
            return;
          }

          const policyData = {
            PolicyName: policy.name,
            PolicyDescription: policy.description,
            Department: policy.department,
            Scope: policy.scope,
            Objective: policy.objective,
            Identifier: policy.identifier,
            CoverageRate: policy.coverageRate,
            Applicability: policy.applicability,
            PolicyType: policy.type,
            PolicyCategory: policy.category,
            PolicySubCategory: policy.subCategory,
            Entities: policy.entities,
            StartDate: policy.startDate,
            EndDate: policy.endDate,
            CreatedByName: policy.createdByName,
            ReviewerName: this.getUserNameById(policy.reviewer),
            subpolicies: [],
            new_subpolicies: []
          };

          // Process subpolicies
          policy.subPolicies.forEach(sp => {
            // Skip excluded subpolicies
            if (sp.exclude) {
              return;
            }

            const subpolicyData = {
              SubPolicyName: sp.name,
              Description: sp.description,
              Identifier: sp.identifier,
              Control: sp.control,
              CreatedByName: sp.createdByName || policy.createdByName
            };

            // Check if it's a new subpolicy or existing one
            if (sp.id && !String(sp.id).startsWith('new-')) {
              // Existing subpolicy
              subpolicyData.original_subpolicy_id = parseInt(sp.id);
              policyData.subpolicies.push(subpolicyData);
            } else {
              // New subpolicy
              policyData.new_subpolicies.push(subpolicyData);
            }
          });

          // Check if it's a new policy or existing one
          if (policy.id && !String(policy.id).startsWith('new-')) {
            // Existing policy
            policyData.original_policy_id = parseInt(policy.id);
            versionData.policies.push(policyData);
          } else {
            // New policy
            versionData.new_policies.push(policyData);
          }
        });

        console.log('Submitting version data:', versionData);
        
        const response = await axios.post(
          `${API_BASE_URL}/api/frameworks/${this.selectedFramework}/create-version/`,
          versionData,
          {
            headers: {
              'Content-Type': 'application/json'
            }
          }
        );

        console.log('Framework version creation response:', response.data);
        
        // Show success message with popup
        PopupService.success('Framework version created successfully!', 'Success');
        
        // Reset form and redirect to framework explorer
        setTimeout(() => {
          this.resetForm();
          this.$router.push('/framework-explorer');
        }, 1500);

      } catch (error) {
        console.error('Error submitting framework version:', error);
        const errorMessage = error.response?.data?.error || 'Failed to submit framework version';
        PopupService.error(errorMessage, 'Error Creating Framework Version');
      } finally {
        this.loading = false;
      }
    },
    validateForm(type) {
      if (type === 'framework') {
        if (!this.frameworkForm.name) {
          PopupService.warning('Framework name is required', 'Validation Error');
          return false;
        }
        if (!this.frameworkForm.description) {
          PopupService.warning('Framework description is required', 'Validation Error');
          return false;
        }
        if (!this.frameworkForm.identifier) {
          PopupService.warning('Framework identifier is required', 'Validation Error');
          return false;
        }
        if (!this.frameworkForm.category) {
          PopupService.warning('Framework category is required', 'Validation Error');
          return false;
        }
        if (!this.frameworkForm.internalExternal) {
          PopupService.warning('Internal/External selection is required', 'Validation Error');
          return false;
        }
        if (!this.frameworkForm.startDate) {
          PopupService.warning('Start date is required', 'Validation Error');
          return false;
        }
        if (!this.frameworkForm.createdByName) {
          PopupService.warning('Created By is required', 'Validation Error');
          return false;
        }
        if (!this.frameworkForm.reviewer) {
          PopupService.warning('Reviewer is required', 'Validation Error');
          return false;
        }

        // Validate that creator and reviewer are not the same person
        if (this.currentUser.UserName && this.frameworkForm.reviewer) {
          const creatorUser = this.users.find(u => u.name === this.currentUser.UserName);
          const reviewerUser = this.users.find(u => u.id === this.frameworkForm.reviewer);
          
          if (creatorUser && reviewerUser && creatorUser.id === reviewerUser.id) {
            PopupService.warning('Creator and reviewer cannot be the same person. Please select a different reviewer.', 'Validation Error');
            return false;
          }
        }
        return true;
      } else if (type === 'policy') {
        const policy = this.policyTabs[this.activePolicyTab];
        if (!policy.name) {
          PopupService.warning('Policy name is required', 'Validation Error');
          return false;
        }
        if (!policy.description) {
          PopupService.warning('Policy description is required', 'Validation Error');
          return false;
        }
        if (!policy.identifier) {
          PopupService.warning('Policy identifier is required', 'Validation Error');
          return false;
        }
        if (!policy.type) {
          PopupService.warning('Policy type is required', 'Validation Error');
          return false;
        }
        if (!policy.category) {
          PopupService.warning('Policy category is required', 'Validation Error');
          return false;
        }
        if (!policy.subCategory) {
          PopupService.warning('Policy sub-category is required', 'Validation Error');
          return false;
        }
        if (!policy.createdByName) {
          PopupService.warning('Created By is required', 'Validation Error');
          return false;
        }
        if (!policy.reviewer) {
          PopupService.warning('Reviewer is required', 'Validation Error');
          return false;
        }

        // Validate that creator and reviewer are not the same person
        if (this.currentUser.UserName && policy.reviewer) {
          const creatorUser = this.users.find(u => u.name === this.currentUser.UserName);
          const reviewerUser = this.users.find(u => u.id === policy.reviewer);
          
          if (creatorUser && reviewerUser && creatorUser.id === reviewerUser.id) {
            PopupService.warning('Creator and reviewer cannot be the same person. Please select a different reviewer.', 'Validation Error');
            return false;
          }
        }
        return true;
      }
      return false;
    },
    resetForm() {
        this.frameworkForm = {
        name: '',
        description: '',
        identifier: '',
        category: '',
        internalExternal: '',
        file: null,
        startDate: '',
        endDate: '',
        createdByName: localStorage.getItem('username') || '', // Use username instead of user_name
        reviewer: ''
      }
        this.policyTabs = []
        this.activePolicyTab = 0
        this.selectedFramework = ''
        this.selectedPolicy = ''
        this.showVersionModal = false
        this.selectedVersionType = 'minor' // Changed from this.versionType to this.selectedVersionType
        this.policies = [] // Clear policies array
        this.previousFrameworkData = null // Clear previous framework data
        this.previousPolicyData = null // Clear previous policy data
        this.frameworkFormLoaded = false
    },
    async submitPolicyVersion() {
      try {
        this.loading = true;
        console.log('Submitting policy version with data:', this.policyTabs[0]);
        
        // Save any new departments and policy categories first
        await this.saveNewDepartments();
        await this.saveNewPolicyCategories();

        // Validate required fields
        if (!this.validateForm('policy')) {
          return;
        }

        // Format data for submission
        const versionData = {
          version_type: this.selectedVersionType,
          PolicyName: this.policyTabs[0].name,
          PolicyDescription: this.policyTabs[0].description,
          Department: this.policyTabs[0].department,
          Scope: this.policyTabs[0].scope,
          Objective: this.policyTabs[0].objective,
          Identifier: this.policyTabs[0].identifier,
          CoverageRate: this.policyTabs[0].coverageRate,
          Applicability: this.policyTabs[0].applicability,
          CreatedByName: this.policyTabs[0].createdByName,
          StartDate: this.policyTabs[0].startDate,
          EndDate: this.policyTabs[0].endDate,
          PermanentTemporary: this.policyTabs[0].permanentTemporary || '',
          DocURL: this.policyTabs[0].docURL || '',
          PolicyType: this.policyTabs[0].type,
          PolicyCategory: this.policyTabs[0].category,
          PolicySubCategory: this.policyTabs[0].subCategory,
          Entities: this.policyTabs[0].entities,
          Reviewer: this.getUserNameById(this.policyTabs[0].reviewer)
        };

        // Handle existing subpolicies
        const subpolicies = [];
        const new_subpolicies = [];

        this.policyTabs[0].subPolicies.forEach(sp => {
          if (sp.id && !String(sp.id).startsWith('new-')) {
            // Existing subpolicy
            subpolicies.push({
              original_subpolicy_id: parseInt(sp.id),
              SubPolicyName: sp.name,
              Description: sp.description,
              Identifier: sp.identifier,
              CreatedByName: sp.createdByName,
              PermanentTemporary: sp.permanentTemporary || '',
              Control: sp.control,
              exclude: sp.exclude || false
            });
          } else if (!sp.exclude) {
            // New subpolicy (only include if not excluded)
            new_subpolicies.push({
              SubPolicyName: sp.name,
              Description: sp.description,
              Identifier: sp.identifier,
              CreatedByName: sp.createdByName,
              PermanentTemporary: sp.permanentTemporary || '',
              Control: sp.control
            });
          }
        });

        versionData.subpolicies = subpolicies;
        versionData.new_subpolicies = new_subpolicies;

        console.log('Submitting version data:', versionData);

        // Make API call to create policy version
        const response = await axios.post(
          `${API_BASE_URL}/api/policies/${this.selectedPolicy}/create-version/`,
          versionData
        );

        console.log('Policy version created:', response.data);
        
        // Show success message with popup
        PopupService.success('Policy version created successfully!', 'Success');
        
        // Reset form and redirect to framework explorer
        setTimeout(() => {
          this.resetForm();
          this.$router.push('/framework-explorer');
        }, 1500);

      } catch (error) {
        console.error('Error creating policy version:', error);
        const errorMessage = error.response?.data?.error || 'Failed to create policy version';
        PopupService.error(errorMessage, 'Error Creating Policy Version');
      } finally {
        this.loading = false;
      }
    },
    async confirmVersionType() {
      this.showVersionModal = false;
      
      try {
        this.loading = true;
        
        // Check if names have been changed based on the selected tab
        if (this.selectedTab === 'framework') {
          // Fetch previous framework data if not already loaded
          if (!this.previousFrameworkData) {
            await this.fetchPreviousFrameworkData();
          }
          
          // Check if framework name has been changed
          
          // Check if any policy names have been changed
          const unchangedPolicies = this.policyTabs
            .filter(policy => !policy.exclude && !String(policy.id).startsWith('new-'))
            .filter(policy => {
              const previousPolicy = this.previousFrameworkData.policies?.find(
                p => p.PolicyId.toString() === policy.id.toString()
              );
              return previousPolicy && policy.name === previousPolicy.PolicyName;
            });
            
          if (unchangedPolicies.length > 0) {
            const policyNames = unchangedPolicies.map(p => p.name).join(', ');
            PopupService.error(
              `You must change the names of all policies when creating a new version. Unchanged policies: ${policyNames}`,
              'Version Error'
            );
            this.loading = false;
            return;
          }
          
          // Check if any subpolicy names have been changed
          let hasUnchangedSubpolicies = false;
          let unchangedSubpolicyNames = [];
          
          for (const policy of this.policyTabs.filter(p => !p.exclude)) {
            if (String(policy.id).startsWith('new-')) continue; // Skip new policies
            
            const previousPolicy = this.previousFrameworkData.policies?.find(
              p => p.PolicyId.toString() === policy.id.toString()
            );
            
            if (!previousPolicy) continue;
            
            for (const subpolicy of policy.subPolicies.filter(sp => !sp.exclude)) {
              if (String(subpolicy.id).startsWith('new-')) continue; // Skip new subpolicies
              
              const previousSubpolicy = previousPolicy.subpolicies?.find(
                sp => sp.SubPolicyId.toString() === subpolicy.id.toString()
              );
              
              if (previousSubpolicy && subpolicy.name === previousSubpolicy.SubPolicyName) {
                hasUnchangedSubpolicies = true;
                unchangedSubpolicyNames.push(`${policy.name} > ${subpolicy.name}`);
              }
            }
          }
          
          if (hasUnchangedSubpolicies) {
            PopupService.error(
              `You must change the names of all subpolicies when creating a new version. Unchanged subpolicies: ${unchangedSubpolicyNames.join(', ')}`,
              'Version Error'
            );
            this.loading = false;
            return;
          }
          
          await this.submitFrameworkVersion();
          
        } else if (this.selectedTab === 'policy') {
          // Fetch previous policy data if not already loaded
          if (!this.previousPolicyData) {
            await this.fetchPreviousPolicyData();
          }
          
          // Check if policy name has been changed
          if (this.previousPolicyData && 
              this.policyTabs[0].name === this.previousPolicyData.PolicyName) {
            PopupService.error(
              'You must change the policy name when creating a new version.',
              'Version Error'
            );
            this.loading = false;
            return;
          }
          
          // Check if any subpolicy names have been changed
          const unchangedSubpolicies = this.policyTabs[0].subPolicies
            .filter(subpolicy => !subpolicy.exclude && !String(subpolicy.id).startsWith('new-'))
            .filter(subpolicy => {
              const previousSubpolicy = this.previousPolicyData.subpolicies?.find(
                sp => sp.SubPolicyId.toString() === subpolicy.id.toString()
              );
              return previousSubpolicy && subpolicy.name === previousSubpolicy.SubPolicyName;
            });
            
          if (unchangedSubpolicies.length > 0) {
            const subpolicyNames = unchangedSubpolicies.map(sp => sp.name).join(', ');
            PopupService.error(
              `You must change the names of all subpolicies when creating a new version. Unchanged subpolicies: ${subpolicyNames}`,
              'Version Error'
            );
            this.loading = false;
            return;
          }
          
          await this.submitPolicyVersion();
        }
      } catch (error) {
        console.error('Error in confirmVersionType:', error);
        PopupService.error('An error occurred while checking version requirements', 'Error');
        this.loading = false;
      }
    },
    
    async fetchPreviousFrameworkData() {
      try {
        if (!this.selectedFramework) return;
        
        const response = await axios.get(`${API_BASE_URL_FULL}/frameworks/${this.selectedFramework}/`);
        console.log('Previous framework data:', response.data);
        
        // Get framework details
        this.previousFrameworkData = response.data;
        
        // Get policies for this framework
        const policiesResponse = await axios.get(`${API_BASE_URL_FULL}/frameworks/${this.selectedFramework}/get-policies/`);
        this.previousFrameworkData.policies = policiesResponse.data;
        
        // Get subpolicies for each policy
        for (const policy of this.previousFrameworkData.policies) {
        const subpoliciesResponse = await axios.get(`${API_BASE_URL_FULL}/policies/${policy.PolicyId}/get-subpolicies/`);
          policy.subpolicies = subpoliciesResponse.data;
        }
        
        console.log('Complete previous framework data with policies and subpolicies:', this.previousFrameworkData);
      } catch (error) {
        console.error('Error fetching previous framework data:', error);
        PopupService.error('Failed to fetch previous framework data', 'Error');
      }
    },
    
    async fetchPreviousPolicyData() {
      try {
        if (!this.selectedPolicy) return;
        
      const response = await axios.get(`${API_BASE_URL_FULL}/policies/${this.selectedPolicy}/`);
        console.log('Previous policy data:', response.data);
        
        // Get policy details
        this.previousPolicyData = response.data;
        
        // Get subpolicies for this policy
      const subpoliciesResponse = await axios.get(`${API_BASE_URL_FULL}/policies/${this.selectedPolicy}/get-subpolicies/`);
        this.previousPolicyData.subpolicies = subpoliciesResponse.data;
        
        console.log('Complete previous policy data with subpolicies:', this.previousPolicyData);
      } catch (error) {
        console.error('Error fetching previous policy data:', error);
        PopupService.error('Failed to fetch previous policy data', 'Error');
      }
    },
    async fetchUsers() {
      try {
        console.log('Fetching users from API...')
        
        // Try the primary endpoint first
        let response
        try {
          response = await axiosInstance.get('/api/users/')
          console.log('Raw users response:', response.data)
        } catch (primaryError) {
          console.error('Primary endpoint failed:', primaryError)
          
          // Try alternative endpoint
          console.log('Trying alternative endpoint...')
          response = await axiosInstance.get('/api/custom-users/')
          console.log('Alternative endpoint response:', response.data)
        }
        
        // Handle both response formats: direct array or success wrapper
        let usersData = []
        if (response.data.success && response.data.users) {
          usersData = response.data.users
        } else if (Array.isArray(response.data)) {
          usersData = response.data
        } else {
          console.error('Unexpected response format:', response.data)
          this.error = 'Invalid response format from users API'
          return
        }
        
        this.users = usersData.map(user => ({
          id: user.UserId,
          name: user.UserName
        }))
        console.log('Mapped users:', this.users)
      } catch (error) {
        console.error('Error fetching users:', error)
        this.error = 'Failed to fetch users'
        PopupService.error('Failed to fetch users', 'Error')
      }
    },

    // Department related methods
    async fetchDepartments() {
      try {
        const response = await axios.get(`${API_ENDPOINTS.DEPARTMENTS}`);
        this.departments = response.data.departments || [];
        console.log('Available departments:', this.departments);
      } catch (error) {
        console.error('Error fetching departments:', error);
        // Provide fallback departments for better user experience
        this.departments = [
          { id: 1, name: 'Information Technology' },
          { id: 2, name: 'Human Resources' },
          { id: 3, name: 'Finance' },
          { id: 4, name: 'Legal' },
          { id: 5, name: 'Operations' },
          { id: 6, name: 'Marketing' },
          { id: 7, name: 'Sales' },
          { id: 8, name: 'Customer Support' }
        ];
        console.log('Using fallback departments due to API error');
        // Don't set error for non-critical API failures
      }
    },

    async saveDepartment(departmentName) {
      try {
        const response = await axios.post(`${API_ENDPOINTS.DEPARTMENTS_SAVE}`, {
          DepartmentName: departmentName,
          EntityId: 1, // Default entity
          DepartmentHead: 1, // Default head
          BusinessUnitId: 1 // Default business unit
        });
        
        if (response.data.success) {
          console.log('Department saved:', response.data.department);
          // Refresh departments list
          await this.fetchDepartments();
          return response.data.department;
        }
      } catch (error) {
        console.error('Error saving department:', error);
        throw error;
      }
    },

    async handleDepartmentChange(idx, value) {
      // Update the policy department value
      this.policyTabs[idx].department = value;
      
      // Check if this is a new department (not in existing list)
      const existingDepartment = this.departments.find(dept => 
        dept.name.toLowerCase() === value.toLowerCase()
      );
      
      if (!existingDepartment && value.trim().length > 0) {
        // This might be a new department, save it when form is submitted
        console.log('New department detected:', value);
      }
    },

    async saveNewDepartments() {
      try {
        console.log('Checking for new departments to save...');
        const newDepartments = [];
        
        // Process all policies to find new departments
        for (const policy of this.policyTabs) {
          const deptName = policy.department?.trim();
          
          if (!deptName) continue;
          
          // Check if this department exists in our local data
          const exists = this.departments.some(dept => 
            dept.name.toLowerCase() === deptName.toLowerCase()
          );
          
          if (!exists && !newDepartments.includes(deptName)) {
            console.log(`Found new department: ${deptName}`);
            newDepartments.push(deptName);
          }
        }
        
        // Save new departments to the database
        if (newDepartments.length > 0) {
          console.log(`Saving ${newDepartments.length} new departments...`);
          
          for (const deptName of newDepartments) {
            await this.saveDepartment(deptName);
          }
          
          console.log('New departments saved successfully');
        } else {
          console.log('No new departments to save');
        }
      } catch (err) {
        console.error('Error saving new departments:', err);
      }
    },

    async saveNewPolicyCategories() {
      try {
        console.log('Checking for new policy categories to save...');
        const newCombinations = [];
        
        // Process all policies to find new category combinations
        for (const policy of this.policyTabs) {
          const type = policy.type?.trim();
          const category = policy.category?.trim();
          const subcategory = policy.subCategory?.trim();
          
          // Skip if any part of the combination is missing
          if (!type || !category || !subcategory) {
            continue;
          }
          
          // Check if this combination exists in our local data
          const exists = this.policyData.some(pc => 
            pc.PolicyType === type && 
            pc.PolicyCategory === category && 
            pc.PolicySubCategory === subcategory
          );
          
          if (!exists) {
            console.log(`Found new combination: ${type} > ${category} > ${subcategory}`);
            const combinationKey = `${type}|${category}|${subcategory}`;
            if (!newCombinations.find(c => `${c.PolicyType}|${c.PolicyCategory}|${c.PolicySubCategory}` === combinationKey)) {
              newCombinations.push({
                PolicyType: type,
                PolicyCategory: category,
                PolicySubCategory: subcategory
              });
            }
          }
        }
        
        // Save new combinations to the database
        if (newCombinations.length > 0) {
          console.log(`Saving ${newCombinations.length} new policy category combinations...`);
          
          for (const combination of newCombinations) {
            // Include framework context when saving policy categories
            const combinationWithFramework = {
              ...combination,
              frameworkId: this.selectedFramework
            };
            console.log('Saving policy category with framework:', combinationWithFramework);
            await axios.post(`${API_BASE_URL}/api/policy-categories/save/`, combinationWithFramework);
          }
          
          // Refresh policy categories after saving
          await this.fetchPolicyData();
          console.log('Policy categories refreshed');
        } else {
          console.log('No new policy category combinations to save');
        }
      } catch (err) {
        console.error('Error saving new policy categories:', err);
      }
    },
    async fetchPolicyDetails(policyId) {
      if (!policyId) return;
      
      try {
        this.loading = true;
        const [policyResponse, subpoliciesResponse] = await Promise.all([
        axios.get(`${API_BASE_URL_FULL}/policies/${policyId}/`),
        axios.get(`${API_BASE_URL_FULL}/policies/${policyId}/get-subpolicies/`)
        ]);

        console.log('Raw policy details:', policyResponse.data);
        console.log('Raw subpolicies:', subpoliciesResponse.data);

        const policy = policyResponse.data;
        
        // Store the previous policy data for version comparison
        this.previousPolicyData = policy;
        this.previousPolicyData.subpolicies = subpoliciesResponse.data;
        
        const currentUsername = this.currentUser.UserName || this.loggedInUsername || '';
        
        // Create a single policy tab with the fetched details
        this.policyTabs = [{
          id: policy.PolicyId,
          name: policy.PolicyName,
          description: policy.PolicyDescription,
          status: policy.Status,
          department: policy.Department,
          scope: policy.Scope,
          objective: policy.Objective,
          identifier: policy.Identifier,
          coverageRate: policy.CoverageRate,
          applicability: policy.Applicability,
          type: policy.PolicyType,
          category: policy.PolicyCategory,
          subCategory: policy.PolicySubCategory,
          entities: policy.Entities,
          startDate: policy.StartDate,
          endDate: policy.EndDate,
          file: null,
          createdByName: currentUsername, // Use current username instead of policy.CreatedByName
          reviewer: '', // Initialize as empty, will be set by user selection
          activeSubPolicyTab: 0,
          subPolicies: subpoliciesResponse.data.map(sp => ({
            id: sp.SubPolicyId,
            name: sp.SubPolicyName,
            identifier: sp.Identifier,
            control: sp.Control,
            description: sp.Description,
            status: sp.Status,
            createdByName: currentUsername // Use current username for subpolicies as well
          }))
        }];

        this.activePolicyTab = 0;
        
      } catch (error) {
        console.error('Error fetching policy details:', error);
        this.error = 'Failed to fetch policy details';
        PopupService.error('Failed to fetch policy details', 'Error');
        this.policyTabs = [];
      } finally {
        this.loading = false;
      }
    },
    excludePolicyTab(idx) {
      // Instead of removing the policy, mark it as excluded
      if (this.policyTabs[idx]) {
        this.policyTabs[idx].exclude = !this.policyTabs[idx].exclude;
        console.log(`Policy ${idx} exclude status:`, this.policyTabs[idx].exclude);
        
        // If excluding, also exclude all subpolicies
        if (this.policyTabs[idx].exclude) {
          this.policyTabs[idx].subPolicies.forEach(subPolicy => {
            subPolicy.exclude = true;
          });
        }
      }
    },
    excludeSubPolicyTab(policyIdx, subIdx) {
      // Toggle exclude status instead of removing
      if (this.policyTabs[policyIdx] && this.policyTabs[policyIdx].subPolicies[subIdx]) {
        this.policyTabs[policyIdx].subPolicies[subIdx].exclude = !this.policyTabs[policyIdx].subPolicies[subIdx].exclude;
      }
    }
    }
  }
  </script>

<style scoped>
.TT-exclude-policy-btn,
.TT-exclude-subpolicy-btn {
padding: 8px 16px;
margin-bottom: 16px;
border: 1px solid #dc3545;
background-color: white;
color: #dc3545;
border-radius: 4px;
cursor: pointer;
transition: all 0.3s ease;
}

.TT-exclude-policy-btn:hover,
.TT-exclude-subpolicy-btn:hover {
background-color: #dc3545;
color: white;
}

.TT-exclude-policy-btn.excluded,
.TT-exclude-subpolicy-btn.excluded {
border-color: #28a745;
color: #28a745;
}

.TT-exclude-policy-btn.excluded:hover,
.TT-exclude-subpolicy-btn.excluded:hover {
background-color: #28a745;
color: white;
}

.TT-policy-tab.excluded,
.TT-subpolicy-tab.excluded {
opacity: 0.6;
background-color: #f8d7da;
border-color: #dc3545;
text-decoration: line-through;
}

.TT-policy-form-container,
.TT-subpolicy-form-container {
position: relative;
transition: opacity 0.3s ease, max-height 0.3s ease;
}

.TT-policy-form-container form,
.TT-subpolicy-form-container form {
transition: opacity 0.3s ease, max-height 0.3s ease;
}

.TT-excluded-message {
text-align: center;
padding: 20px;
color: #721c24;
background-color: #f8d7da;
border: 1px solid #f5c6cb;
border-radius: 4px;
margin: 10px 0;
}

.version-modal-overlay {
position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.version-modal {
background: #fff; padding: 2rem 2.5rem; border-radius: 12px; min-width: 350px; box-shadow: 0 2px 16px rgba(0,0,0,0.15);
}
.version-type-options {
display: flex; gap: 2rem; margin: 1.5rem 0;
}
.version-type-option {
display: flex; flex-direction: column; align-items: center; cursor: pointer; position: relative;
}
.version-type-option input[type="radio"] {
display: none;
}
.radio-custom {
width: 28px; height: 28px; border: 2px solid #3b6cf6; border-radius: 50%; margin-bottom: 0.5rem; display: flex; align-items: center; justify-content: center;
background: #fff;
}
.radio-custom.checked {
background: #3b6cf6;
box-shadow: 0 0 0 2px #3b6cf6;
}
.version-type-title {
font-weight: bold; font-size: 1.2rem; margin-bottom: 0.3rem;
}
.version-type-desc {
color: #666; text-align: center; font-size: 1rem;
}
.version-type-example {
color: #aaa; font-size: 0.95rem;
}
.version-modal-actions {
display: flex; justify-content: flex-end; gap: 1rem; margin-top: 2rem;
}
.version-modal-actions button {
padding: 0.5rem 1.2rem; 
border: none; 
border-radius: 4px; 
font-weight: bold; 
cursor: pointer;
min-width: 80px;
transition: all 0.2s ease;
}
.version-modal-actions .btn-primary {
background: #3b6cf6; 
color: #fff;
}
.version-modal-actions .btn-primary:hover {
background: #2951c3;
}
.version-modal-actions .btn-secondary {
background: #e0e0e0;
color: #333;
}
.version-modal-actions .btn-secondary:hover {
background: #d0d0d0;
}
.version-modal-actions button:disabled {
opacity: 0.7;
cursor: not-allowed;
}

/* Entity Dropdown Styles */
.entities-group {
width: 100%;
}

.entities-multi-select {
position: relative;
width: 100%;
}

.entities-dropdown {
width: 100%;
}

.selected-entities {
border: 1px solid #ccc;
border-radius: 4px;
padding: 8px 12px;
cursor: pointer;
display: flex;
justify-content: space-between;
align-items: center;
background: #fff;
min-height: 40px;
}

.selected-entities.active {
border-color: #3b6cf6;
}

.selected-entities.error {
border-color: #dc3545;
}

.entity-content {
flex: 1;
overflow: hidden;
text-overflow: ellipsis;
white-space: nowrap;
}

.entity-tag {
background: #e9ecef;
padding: 2px 8px;
border-radius: 4px;
margin-right: 4px;
font-size: 0.9em;
}

.all-tag {
background: #3b6cf6;
color: #fff;
}

.placeholder {
color: #6c757d;
}

.dropdown-arrow {
margin-left: 8px;
transition: transform 0.2s;
}

.active .dropdown-arrow {
transform: rotate(180deg);
}

.entities-options {
position: absolute;
top: 100%;
left: 0;
right: 0;
background: #fff;
border: 1px solid #ccc;
border-radius: 4px;
margin-top: 4px;
max-height: 200px;
overflow-y: auto;
z-index: 1000;
box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.entity-option {
padding: 8px 12px;
cursor: pointer;
display: flex;
align-items: center;
transition: background 0.2s;
}

.entity-option:hover {
background: #f8f9fa;
}

.entity-option input[type="checkbox"] {
margin-right: 8px;
}

.entity-label {
flex: 1;
}

.all-option {
border-bottom: 1px solid #dee2e6;
font-weight: bold;
}

.entities-loading,
.entities-error {
padding: 12px;
text-align: center;
color: #6c757d;
}

.entities-error {
color: #dc3545;
}

/* Auto-generated label styling */
.auto-generated-label {
font-size: 0.85em;
color: #6c757d;
font-weight: normal;
font-style: italic;
margin-left: 5px;
}

/* Refresh button styling */
.VV-page-header {
display: flex;
justify-content: space-between;
align-items: center;
margin-bottom: 5px;
}

.VV-refresh-btn {
background: #3b6cf6;
color: white;
border: none;
padding: 8px 16px;
border-radius: 4px;
cursor: pointer;
display: flex;
align-items: center;
gap: 8px;
font-size: 14px;
transition: all 0.3s ease;
}

.VV-refresh-btn:hover {
background: #2951c3;
}

.VV-refresh-btn:disabled {
background: #ccc;
cursor: not-allowed;
}

.VV-refresh-btn i {
font-size: 14px;
}

.fa-spin {
animation: spin 1s linear infinite;
}

@keyframes spin {
from { transform: rotate(0deg); }
to { transform: rotate(360deg); }
}

/* Error message styling */
.VV-error-message {
background: #f8d7da;
color: #721c24;
border: 1px solid #f5c6cb;
border-radius: 4px;
padding: 12px;
margin-bottom: 16px;
display: flex;
align-items: center;
gap: 8px;
}

.VV-error-message i {
color: #dc3545;
}

.VV-retry-btn {
background: #dc3545;
color: white;
border: none;
padding: 4px 8px;
border-radius: 4px;
cursor: pointer;
font-size: 12px;
margin-left: auto;
}

.VV-retry-btn:hover {
background: #c82333;
}

/* Loading message styling */
.VV-loading-message {
background: #d1ecf1;
color: #0c5460;
border: 1px solid #bee5eb;
border-radius: 4px;
padding: 12px;
margin-bottom: 16px;
display: flex;
align-items: center;
gap: 8px;
}

.VV-loading-message i {
color: #17a2b8;
}

/* Dropdown button styling - reduce padding and white background */
:deep(.VV-top-dropdowns .dropdown-container .filter-btn) {
  background: white !important;
  padding: 3px 6px !important;
  border: 1px solid #ddd !important;
  border-radius: 6px !important;
  box-shadow: none !important;
}

:deep(.VV-top-dropdowns .dropdown-container .filter-btn:hover) {
  background: white !important;
  border-color: #ddd !important;
  box-shadow: none !important;
}

/* Dropdown menu container with single border */
:deep(.VV-top-dropdowns .dropdown-container .dropdown-menu) {
  background: white !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 8px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
  padding: 4px !important;
}

/* Dropdown items without individual borders */
:deep(.VV-top-dropdowns .dropdown-container .dropdown-item) {
  background: white !important;
  border: none !important;
  border-radius: 4px !important;
  margin-bottom: 2px !important;
  white-space: normal !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  font-size: 0.8em !important;
  font-weight: normal !important;
  line-height: 1.3 !important;
  padding: 6px 10px !important;
  max-width: 100% !important;
}

:deep(.VV-top-dropdowns .dropdown-container .dropdown-item:hover) {
  background: #f8f9fa !important;
}

/* Fix dropdown content overflow and text wrapping */
:deep(.VV-top-dropdowns .dropdown-container .dropdown-menu) {
  max-height: 300px !important;
  overflow-y: auto !important;
}

:deep(.VV-top-dropdowns .dropdown-container .dropdown-item) {
  white-space: normal !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  font-size: 0.75em !important;
  line-height: 1.3 !important;
  padding: 6px 10px !important;
  max-width: 100% !important;
}

/* Policy Type Dropdown */
.policy-type-options {
  max-height: 250px !important;
  overflow-y: auto !important;
}

.policy-type-option {
  white-space: normal !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  font-size: 0.75em !important;
  line-height: 1.3 !important;
  padding: 6px 10px !important;
}

.policy-type-label {
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  max-width: 100% !important;
}

/* Policy Category Dropdown */
.policy-category-options {
  max-height: 250px !important;
  overflow-y: auto !important;
}

.policy-category-option {
  white-space: normal !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  font-size: 0.75em !important;
  line-height: 1.3 !important;
  padding: 6px 10px !important;
}

.policy-category-label {
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  max-width: 100% !important;
}

/* Policy Subcategory Dropdown */
.policy-subcategory-options {
  max-height: 250px !important;
  overflow-y: auto !important;
}

.policy-subcategory-option {
  white-space: normal !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  font-size: 0.75em !important;
  line-height: 1.3 !important;
  padding: 6px 10px !important;
}

.policy-subcategory-label {
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  max-width: 100% !important;
}

/* Entities Dropdown */
.entities-options {
  max-height: 250px !important;
  overflow-y: auto !important;
}

.entity-option {
  white-space: normal !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  font-size: 0.75em !important;
  line-height: 1.3 !important;
}

.entity-label {
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  max-width: 100% !important;
}

/* Search input container */
.search-input-container {
  padding: 6px !important;
}

.search-input {
  font-size: 0.75em !important;
  width: 100% !important;
  box-sizing: border-box !important;
}
</style>
