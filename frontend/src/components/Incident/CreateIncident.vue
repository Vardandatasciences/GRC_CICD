<template>
  <div class="incident-form-page incident">
    <!-- Page Header with Back Button and Title -->
    <div class="incident-form-page-header">
      <div class="incident-header-content">
        <div class="incident-header-left">
          <router-link to="/incident/incident" class="incident-back-link">
            <i class="fas fa-arrow-left"></i>
          </router-link>
          <h1 class="incident-form-page-title">Create Incident</h1>
        </div>
        <div class="incident-header-actions">
          <button type="button" @click="generateAnalysis" class="generate-analysis-btn" :disabled="isGeneratingAnalysis" style="color: white;">
            Generate Analysis
          </button>
        </div>
      </div>
    </div>

    <div class="incident-form-box">
      <form @submit.prevent="validateAndSubmit" class="incident-create-form">
        <!-- Incident Title and Description Section -->
        <div class="incident-title-description-section">
          <div class="section-header">
            <h3>Incident Overview</h3>
          </div>
          
          <div class="title-description-fields">
            <label class="field-title required">
              <span>Incident Title</span>
              <input 
                type="text" 
                v-model="formData.IncidentTitle" 
                @input="validateIncidentTitle"
                @blur="validateIncidentTitle"
                :aria-invalid="!!validationErrors.IncidentTitle"
                :class="{ 'error': validationErrors.IncidentTitle }"
                placeholder="e.g., Database Server Outage, Unauthorized Access to Customer Data, Phishing Email Incident..."
                title="Provide a clear, concise title that summarizes the incident. Include key systems or data affected."
                required 
              />

              <div v-if="validationErrors.IncidentTitle" class="validation-error">{{ validationErrors.IncidentTitle }}</div>
            </label>

            <label class="field-description required">
              <span>Description</span>
              <textarea 
                v-model="formData.Description" 
                @input="validateDescription"
                @blur="validateDescription"
                :aria-invalid="!!validationErrors.Description"
                :class="{ 'error': validationErrors.Description }"
                placeholder="Describe what happened in detail: What was the nature of the incident? How was it discovered? What systems or processes were affected? Include timeline if known. Be specific about the sequence of events, who discovered it, and immediate actions taken..."
                title="Provide a comprehensive description of the incident including what happened, when, how it was discovered, and what systems/processes were affected."
                required
                style="min-height: 120px; height: 120px; resize: vertical; padding: 12px; line-height: 1.5; font-size: 14px;"
              ></textarea>

              <div v-if="validationErrors.Description" class="validation-error">{{ validationErrors.Description }}</div>
            </label>
          </div>
        </div>

        <!-- Basic Information Section -->
        <label class="field-third">
          <span>Origin</span>
          <select v-model="formData.Origin" @change="validateOrigin" 
                  :aria-invalid="!!validationErrors.Origin"
                  :class="{ 'error': validationErrors.Origin }"
                  title="Select how this incident was discovered or reported - Manual or System Generated">
            <option value="">Select how incident was discovered...</option>
            <option value="Manual">Manual</option>
            <option value="System Generated">System Generated</option>
          </select>
          <div v-if="validationErrors.Origin" class="validation-error">{{ validationErrors.Origin }}</div>
        </label>

        <label class="field-third required">
          <span>Date</span>
          <input 
            type="date" 
            v-model="formData.Date" 
            @input="validateDate"
            @blur="validateDate"
            :aria-invalid="!!validationErrors.Date"
            :class="{ 'error': validationErrors.Date }"
            title="Date when the incident occurred or was first discovered. Use the actual incident date if known, or discovery date if incident date is unknown."
            required 
          />
          <div v-if="validationErrors.Date" class="validation-error">{{ validationErrors.Date }}</div>
        </label>

        <label class="field-third required">
          <span>Time</span>
          <input 
            type="time" 
            v-model="formData.Time" 
            @input="validateTime"
            @blur="validateTime"
            :aria-invalid="!!validationErrors.Time"
            :class="{ 'error': validationErrors.Time }"
            title="Time when the incident occurred or was first discovered. Use 24-hour format. If exact time is unknown, provide approximate time."
            required 
          />
          <div v-if="validationErrors.Time" class="validation-error">{{ validationErrors.Time }}</div>
        </label>
        
        <label class="field-third required">
          <span>Risk Priority</span>
          <select v-model="formData.RiskPriority" @change="validateRiskPriority" 
                  :aria-invalid="!!validationErrors.RiskPriority"
                  :class="{ 'error': validationErrors.RiskPriority, 'priority-select': true }"
                  title="Assess the severity level: High (critical systems, data breach, major outage), Medium (limited impact, some systems affected), Low (minor issues, no critical impact)" required>
            <option value="">Assess the severity level of this incident...</option>
            <option value="High">High - Critical systems/data affected</option>
            <option value="Medium">Medium - Limited impact, some systems affected</option>
            <option value="Low">Low - Minor issues, no critical impact</option>
          </select>
          <div v-if="validationErrors.RiskPriority" class="validation-error">{{ validationErrors.RiskPriority }}</div>
        </label>
        
        <!-- Risk and Impact Section -->
        <label class="field-third required">
          <span>Risk Category</span>
          <div class="multi-select-dropdown" :class="{ 'error': validationErrors.RiskCategory }">
            <div class="multi-select-input" @click="toggleCategoryDropdown" 
                 :aria-invalid="!!validationErrors.RiskCategory"
                 :class="{ 'error': validationErrors.RiskCategory }">
              <div class="selected-items">
                <span v-if="selectedCategories.length === 0" class="placeholder">
                  Select categories or type to add new...
                </span>
                <span v-for="category in selectedCategories" :key="category" class="selected-item">
                  {{ category }}
                  <i class="fas fa-times" @click.stop="removeCategory(category)"></i>
                </span>
              </div>
              <i class="fas fa-chevron-down dropdown-arrow" :class="{ 'rotated': showCategoryDropdown }"></i>
            </div>
            <div v-if="showCategoryDropdown" class="dropdown-panel">
              <div class="search-box">
                <input 
                  type="text" 
                  v-model="categorySearchTerm" 
                  @input="filterCategories"
                  @keydown.enter.prevent="addCustomCategory"
                  placeholder="Search categories or type new..."
                  class="search-input"
                />
                <button v-if="categorySearchTerm && !availableCategories.includes(categorySearchTerm)" 
                        type="button"
                        @click.stop="addCustomCategory" 
                        class="add-new-btn">
                  <i class="fas fa-plus"></i> Add "{{ categorySearchTerm }}"
                </button>
              </div>
              <div class="options-list">
                <div v-if="filteredCategories.length === 0 && !categorySearchTerm" class="no-options">
                  No categories available
                </div>
                <div v-for="category in filteredCategories" 
                     :key="category" 
                     class="option-item" 
                     @click="toggleCategory(category)">
                  <input type="checkbox" :checked="selectedCategories.includes(category)" />
                  <span>{{ category }}</span>
                </div>
              </div>
            </div>
          </div>
          <div v-if="validationErrors.RiskCategory" class="validation-error">{{ validationErrors.RiskCategory }}</div>
        </label>
        
        <label class="field-third">
          <span>Criticality</span>
          <select v-model="formData.Criticality" @change="validateCriticality" 
                  :aria-invalid="!!validationErrors.Criticality"
                  :class="{ 'error': validationErrors.Criticality }"
                  title="Rate the overall criticality: Critical , High , Medium , Low">
            <option value="">Rate the overall criticality level...</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
          <div v-if="validationErrors.Criticality" class="validation-error">{{ validationErrors.Criticality }}</div>
        </label>

        <label class="field-third">
          <span>Cost of Incident</span>
          <div class="cost-field-container">
            <input 
              type="number" 
              v-model.number="formData.CostOfIncident" 
              @input="validateCost" 
              @blur="validateCost"
              :aria-invalid="!!validationErrors.CostOfIncident"
              :class="{ 'error': validationErrors.CostOfIncident }"
              placeholder="50000"
              title="Enter the estimated financial impact as a numeric value"
              min="0"
              step="any"
            />
            <div 
              v-if="formData.CostJustification" 
              class="ai-badge"
              :title="formData.CostJustification"
            >AI</div>
          </div>

          <div v-if="validationErrors.CostOfIncident" class="validation-error">{{ validationErrors.CostOfIncident }}</div>
        </label>

        <label class="field-third">
          <span>Possible Damage</span>
          <textarea 
            v-model="formData.PossibleDamage"
            @input="validatePossibleDamage"
            @blur="validatePossibleDamage"
            placeholder="Describe potential damage: Data loss, customer trust impact, regulatory fines, business disruption, reputation damage, legal liability, service outages, security vulnerabilities exposed..."
            title="Detail all potential damage from this incident: immediate impacts, long-term consequences, regulatory implications, reputation effects, etc."
            style="min-height: 150px; height: 150px; resize: vertical; padding: 10px; line-height: 1.4; font-size: 14px;"
          ></textarea>

          <div v-if="validationErrors.PossibleDamage" class="validation-error">{{ validationErrors.PossibleDamage }}</div>
        </label>

        <label class="field-third">
          <span>Business Unit</span>
          <div class="multi-select-dropdown">
            <div class="multi-select-input" @click="toggleBusinessUnitDropdown">
              <div class="selected-items">
                <span v-if="selectedBusinessUnits.length === 0" class="placeholder">
                  Select business units or type to add new...
                </span>
                <span v-for="unit in selectedBusinessUnits" :key="unit" class="selected-item">
                  {{ unit }}
                  <i class="fas fa-times" @click.stop="removeBusinessUnit(unit)"></i>
                </span>
              </div>
              <i class="fas fa-chevron-down dropdown-arrow" :class="{ 'rotated': showBusinessUnitDropdown }"></i>
            </div>
            <div v-if="showBusinessUnitDropdown" class="dropdown-panel">
              <div class="search-box">
                <input 
                  type="text" 
                  v-model="businessUnitSearchTerm" 
                  @input="filterBusinessUnits"
                  @keydown.enter.prevent="addCustomBusinessUnit"
                  placeholder="Search business units or type new..."
                  class="search-input"
                />
                <button v-if="businessUnitSearchTerm && !availableBusinessUnits.includes(businessUnitSearchTerm)" 
                        type="button"
                        @click.stop="addCustomBusinessUnit" 
                        class="add-new-btn">
                  <i class="fas fa-plus"></i> Add "{{ businessUnitSearchTerm }}"
                </button>
              </div>
              <div class="options-list">
                <div v-if="filteredBusinessUnits.length === 0 && !businessUnitSearchTerm" class="no-options">
                  No business units available
                </div>
                <div v-for="unit in filteredBusinessUnits" 
                     :key="unit" 
                     class="option-item" 
                     @click="toggleBusinessUnit(unit)">
                  <input type="checkbox" :checked="selectedBusinessUnits.includes(unit)" />
                  <span>{{ unit }}</span>
                </div>
              </div>
            </div>
          </div>
          <div v-if="validationErrors.AffectedBusinessUnit" class="validation-error">{{ validationErrors.AffectedBusinessUnit }}</div>
        </label>

        <label class="field-third">
          <span>Location</span>
          <input 
            type="text" 
            v-model="formData.GeographicLocation"
            @input="validateGeographicLocation"
            @blur="validateGeographicLocation"
            placeholder="e.g., New York Office, London Branch, Remote/Cloud, Data Center - Dallas, Building A Floor 3..."
            title="Specify the physical or logical location where the incident occurred: office locations, data centers, cloud regions, or remote locations."
          />

          <div v-if="validationErrors.GeographicLocation" class="validation-error">{{ validationErrors.GeographicLocation }}</div>
        </label>

        <label class="field-third">
          <span>Systems Involved</span>
          <input 
            type="text" 
            v-model="formData.SystemsAssetsInvolved"
            @input="validateSystemsInvolved"
            @blur="validateSystemsInvolved"
            placeholder="e.g., Customer CRM, Payment Gateway, Email Server, Database XYZ, Network Infrastructure, ERP System..."
            title="List all systems, applications, databases, networks, or assets involved in or affected by this incident."
          />

          <div v-if="validationErrors.SystemsAssetsInvolved" class="validation-error">{{ validationErrors.SystemsAssetsInvolved }}</div>
        </label>

        <label class="field-third">
          <span>Incident Classification</span>
          <select v-model="formData.IncidentClassification" @change="onClassificationChange" title="Classify the type of incident: NonConformance, Control GAP, Risk, No Issue">
            <option value="">Classify the type of incident...</option>
            <option value="NonConformance">NonConformance</option>
            <option value="Control GAP">Control GAP</option>
            <option value="Risk">Risk</option>
            <option value="Issue">No Issue</option>
          </select>
        </label>

        <label class="field-third">
          <span>Incident Category</span>
          <div class="multi-select-dropdown" :class="{ 'error': validationErrors.IncidentCategory }">
            <div class="multi-select-input" @click="toggleIncidentCategoryDropdown" 
                 :aria-invalid="!!validationErrors.IncidentCategory"
                 :class="{ 'error': validationErrors.IncidentCategory }">
              <div class="selected-items">
                <span v-if="selectedIncidentCategories.length === 0" class="placeholder">
                  Select incident categories or type to add new...
                </span>
                <span v-for="category in selectedIncidentCategories" :key="category" class="selected-item">
                  {{ category }}
                  <i class="fas fa-times" @click.stop="removeIncidentCategory(category)"></i>
                </span>
              </div>
              <i class="fas fa-chevron-down dropdown-arrow" :class="{ 'rotated': showIncidentCategoryDropdown }"></i>
            </div>
            <div v-if="showIncidentCategoryDropdown" class="dropdown-panel">
              <div class="search-box">
                <input 
                  type="text" 
                  v-model="incidentCategorySearchTerm" 
                  @input="filterIncidentCategories"
                  @keydown.enter.prevent="addCustomIncidentCategory"
                  placeholder="Search incident categories or type new..."
                  class="search-input"
                />
                <button v-if="incidentCategorySearchTerm && !availableIncidentCategories.includes(incidentCategorySearchTerm)" 
                        type="button"
                        @click.stop="addCustomIncidentCategory" 
                        class="add-new-btn">
                  <i class="fas fa-plus"></i> Add "{{ incidentCategorySearchTerm }}"
                </button>
              </div>
              <div class="options-list">
                <div v-if="filteredIncidentCategories.length === 0 && !incidentCategorySearchTerm" class="no-options">
                  No incident categories available
                </div>
                <div v-for="category in filteredIncidentCategories" 
                     :key="category" 
                     class="option-item" 
                     @click="toggleIncidentCategory(category)">
                  <input type="checkbox" :checked="selectedIncidentCategories.includes(category)" />
                  <span>{{ category }}</span>
                </div>
              </div>
            </div>
          </div>
          <div v-if="validationErrors.IncidentCategory" class="validation-error">{{ validationErrors.IncidentCategory }}</div>
        </label>

        <!-- Compliance Mapping Section (shown only when NonConformance or GAP is selected) -->
        <div v-if="showComplianceMapping" class="field-full compliance-mapping-section">
          <label class="field-full">
            <span>Map to Existing Compliance</span>
            <div class="compliance-selector" @click.stop>
              <input 
                type="text" 
                v-model="complianceSearchTerm" 
                placeholder="Search compliances by description, policy name, framework, or compliance ID to link with this incident..."
                @input="filterCompliances"
                @focus="showDropdown = true"
                @blur="hideDropdownDelayed"
                class="compliance-search"
                title="Search and select a compliance requirement to link with this incident. You can search by compliance description, policy name, framework name, or compliance identifier."
              />
              <div v-if="loadingCompliances" class="compliance-loading">
                <i class="fas fa-spinner fa-spin"></i> Loading compliances...
              </div>
              <div v-else-if="compliances.length === 0" class="no-compliances-available">
                <div class="external-risk-message">
                  <i class="fas fa-exclamation-triangle"></i>
                  <div>
                    <strong>No Compliances Available</strong>
                    <p>This incident will be saved as an <strong>External Risk</strong> since no compliance items are available in the system.</p>
                  </div>
                </div>
              </div>
              <div v-else-if="showDropdown && filteredCompliances.length > 0" class="compliance-dropdown">
                <div v-if="!complianceSearchTerm" class="compliance-info">
                  <small><i class="fas fa-info-circle"></i> Showing {{ filteredCompliances.length }} total compliances. Use search to filter results.</small>
                </div>
                <div v-else class="compliance-info">
                  <small><i class="fas fa-search"></i> Found {{ filteredCompliances.length }} compliance(s) matching "{{ complianceSearchTerm }}"</small>
                </div>
                <div class="compliance-options-container">
                  <div 
                    v-for="compliance in filteredCompliances" 
                    :key="compliance.ComplianceId"
                    @click="selectCompliance(compliance)"
                    class="compliance-option"
                    :class="{ 'selected': formData.ComplianceId === compliance.ComplianceId }"
                  >
                    <div class="compliance-checkbox">
                      <input 
                        type="radio" 
                        :id="'compliance-' + compliance.ComplianceId"
                        :value="compliance.ComplianceId"
                        :checked="formData.ComplianceId === compliance.ComplianceId"
                        @click.stop
                        @change="selectCompliance(compliance)"
                      />
                      <label :for="'compliance-' + compliance.ComplianceId" class="radio-label"></label>
                    </div>
                    <div class="compliance-content">
                      <div class="compliance-header">
                        <strong>{{ compliance.ComplianceItemDescription }}</strong>
                        <span class="compliance-criticality" :class="'criticality-' + (compliance.Criticality || 'medium').toLowerCase()">
                          {{ compliance.Criticality }}
                        </span>
                      </div>
                      <div class="compliance-details">
                        <span class="framework-name">{{ compliance.SubPolicy?.Policy?.Framework?.FrameworkName || 'No Framework' }}</span>
                        <span class="policy-name">{{ compliance.SubPolicy?.Policy?.PolicyName || 'No Policy' }}</span>
                      </div>
                      <div v-if="compliance.Mitigation && typeof compliance.Mitigation === 'string'" class="compliance-mitigation">
                        <small>{{ safeSubstring(compliance.Mitigation, 100) }}</small>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else-if="!loadingCompliances && complianceSearchTerm && showDropdown" class="no-compliances">
                No compliances found matching "{{ complianceSearchTerm }}"
              </div>
            </div>
          </label>
          
          <!-- Selected Compliance Display -->
          <div v-if="selectedCompliance" class="selected-compliance">
            <h4><i class="fas fa-check-circle"></i> Selected Compliance</h4>
            <div class="compliance-card">
              <div class="compliance-card-header">
                <strong>{{ selectedCompliance.ComplianceItemDescription }}</strong>
                <span class="compliance-criticality" :class="'criticality-' + (selectedCompliance.Criticality || 'medium').toLowerCase()">
                  {{ selectedCompliance.Criticality }}
                </span>
              </div>
              <div class="compliance-card-body">
                <p><strong>Framework:</strong> {{ selectedCompliance.SubPolicy?.Policy?.Framework?.FrameworkName || 'N/A' }}</p>
                <p><strong>Policy:</strong> {{ selectedCompliance.SubPolicy?.Policy?.PolicyName || 'N/A' }}</p>
                <p><strong>Sub Policy:</strong> {{ selectedCompliance.SubPolicy?.SubPolicyName || 'N/A' }}</p>
                <p v-if="selectedCompliance.Mitigation && typeof selectedCompliance.Mitigation === 'string'"><strong>Mitigation:</strong> {{ selectedCompliance.Mitigation }}</p>
                <p v-if="selectedCompliance.PossibleDamage && typeof selectedCompliance.PossibleDamage === 'string'"><strong>Possible Damage:</strong> {{ selectedCompliance.PossibleDamage }}</p>
              </div>
              <button type="button" @click="clearCompliance" class="clear-compliance-btn">
                <i class="fas fa-times"></i> Clear Selection
              </button>
            </div>
          </div>
        </div>

        <label class="field-third">
          <span>Initial Impact Assessment</span>
          <textarea 
            v-model="formData.InitialImpactAssessment"
            @input="validateInitialImpact"
            @blur="validateInitialImpact"
            placeholder="Describe immediate and potential impacts: operational disruption (services down for 2 hours), customer impact (500 users affected), data exposure (personal data accessed), service availability (website 50% slower), compliance implications (GDPR breach), financial impact..."
            title="Assess all impacts: operational disruption, customer effects, data exposure, service availability, compliance violations, financial consequences, reputation damage."
            style="min-height: 150px; height: 150px; resize: vertical; padding: 10px; line-height: 1.4; font-size: 14px;"
          ></textarea>

          <div v-if="validationErrors.InitialImpactAssessment" class="validation-error">{{ validationErrors.InitialImpactAssessment }}</div>
        </label>

        <label class="field-third">
          <span>Mitigation Steps</span>
          <textarea 
            v-model="formData.Mitigation"
            @input="validateMitigation"
            @blur="validateMitigation"
            placeholder="Detail immediate actions taken and planned steps: containment measures (isolated affected systems), system isolation (disconnected server X), patches applied (security update installed), temporary workarounds (manual process activated), notifications sent..."
            title="Document all mitigation actions: immediate containment steps, system changes, patches applied, workarounds implemented, and planned remediation activities."
            style="min-height: 150px; height: 150px; resize: vertical; padding: 10px; line-height: 1.4; font-size: 14px;"
          ></textarea>

          <div v-if="validationErrors.Mitigation" class="validation-error">{{ validationErrors.Mitigation }}</div>
        </label>

        <label class="field-third">
          <span>Comments</span>
          <textarea 
            v-model="formData.Comments"
            @input="validateComments"
            @blur="validateComments"
            placeholder="Additional observations, context, or relevant information: unusual circumstances, related incidents, external factors, stakeholder communications, lessons learned during response..."
            title="Include any additional context, observations, related incidents, external factors, or other relevant information not covered in other fields."
            style="min-height: 150px; height: 150px; resize: vertical; padding: 10px; line-height: 1.4; font-size: 14px;"
          ></textarea>

          <div v-if="validationErrors.Comments" class="validation-error">{{ validationErrors.Comments }}</div>
        </label>
        
        <label class="field-third">
          <span>Internal Contacts</span>
          <textarea 
            v-model="formData.InternalContacts"
            @input="validateInternalContacts"
            @blur="validateInternalContacts"
            placeholder="Names and roles of internal staff involved: John Smith (IT Manager), Sarah Jones (Security Lead), Mike Wilson (Database Admin), incident response team members, management notified..."
            title="List internal employees involved in the incident response, discovery, or affected by the incident. Include names and their roles/departments."
            style="min-height: 80px; height: 80px; resize: vertical; padding: 10px; line-height: 1.4; font-size: 14px;"
          ></textarea>

          <div v-if="validationErrors.InternalContacts" class="validation-error">{{ validationErrors.InternalContacts }}</div>
        </label>
        
        <label class="field-third">
          <span>External Parties</span>
          <textarea 
            v-model="formData.ExternalPartiesInvolved"
            @input="validateExternalParties"
            @blur="validateExternalParties"
            placeholder="External organizations, vendors, customers affected: ABC Vendor (cloud provider), Customer Portal Users, Third-party Service Provider XYZ, law enforcement, insurance company, audit firm..."
            title="List external organizations, vendors, customers, partners, or third parties affected by or involved in the incident response."
            style="min-height: 80px; height: 80px; resize: vertical; padding: 10px; line-height: 1.4; font-size: 14px;"
          ></textarea>

          <div v-if="validationErrors.ExternalPartiesInvolved" class="validation-error">{{ validationErrors.ExternalPartiesInvolved }}</div>
        </label>
        
        <label class="field-third">
          <span>Regulatory Bodies</span>
          <textarea 
            v-model="formData.RegulatoryBodies"
            @input="validateRegulatoryBodies"
            @blur="validateRegulatoryBodies"
            placeholder="Relevant regulatory authorities that may need notification: SEC, GDPR Authority, FINRA, HIPAA, PCI DSS Council, local data protection authority, industry regulators..."
            title="List regulatory bodies that may need to be notified about this incident based on compliance requirements and data protection laws."
            style="min-height: 80px; height: 80px; resize: vertical; padding: 10px; line-height: 1.4; font-size: 14px;"
          ></textarea>

          <div v-if="validationErrors.RegulatoryBodies" class="validation-error">{{ validationErrors.RegulatoryBodies }}</div>
        </label>
        
        <!-- Additional Information -->
        <label class="field-third">
          <span>Violated Policies/Procedures</span>
          <textarea 
            v-model="formData.RelevantPoliciesProceduresViolated"
            @input="validateViolatedPolicies"
            @blur="validateViolatedPolicies"
            placeholder="List specific policies, procedures, or standards violated: Data Protection Policy section 3.2, Access Control Procedure, Change Management Process, Password Policy, Security Awareness Training requirements..."
            title="Document specific organizational policies, procedures, standards, or compliance requirements that were violated or not followed during this incident."
            style="min-height: 150px; height: 150px; resize: vertical; padding: 10px; line-height: 1.4; font-size: 14px;"
          ></textarea>

          <div v-if="validationErrors.RelevantPoliciesProceduresViolated" class="validation-error">{{ validationErrors.RelevantPoliciesProceduresViolated }}</div>
        </label>
        
        <label class="field-third">
          <span>Control Failures</span>
          <textarea 
            v-model="formData.ControlFailures"
            @input="validateControlFailures"
            @blur="validateControlFailures"
            placeholder="Identify failed controls: firewall misconfiguration, inadequate access controls, missing monitoring alerts, failed backup procedures, insufficient logging, weak authentication, missing patches..."
            title="Document specific security controls, technical controls, or procedural controls that failed or were bypassed during this incident."
            style="min-height: 150px; height: 150px; resize: vertical; padding: 10px; line-height: 1.4; font-size: 14px;"
          ></textarea>

          <div v-if="validationErrors.ControlFailures" class="validation-error">{{ validationErrors.ControlFailures }}</div>
        </label>
        
        <label class="field-third">
          <span>Lessons Learned</span>
          <textarea 
            v-model="formData.LessonsLearned"
            placeholder="Document key insights and lessons: What can be learned from this incident? What should be done differently next time? What processes need improvement? What preventive measures can be implemented? Training gaps identified, process improvements needed..."
            title="Document insights and lessons learned from this incident for future prevention and improved incident response procedures."
            style="min-height: 150px; height: 150px; resize: vertical; padding: 10px; line-height: 1.4; font-size: 14px;"
          ></textarea>

        </label>

        <!-- Incident Status Information -->
        <div v-if="showComplianceMapping" class="incident-status-info">
          <div class="status-header">
            <i class="fas fa-info-circle"></i>
            <strong>Incident Information</strong>
          </div>
          <div class="status-details">
            <div class="status-item">
              <span class="label">Type:</span>
              <span class="value" :class="'incident-type-' + incidentType.toLowerCase().replace(/[^a-z]/g, '-')">
                {{ incidentType }}
              </span>
            </div>
            <div v-if="selectedCompliance" class="status-item">
              <span class="label">Linked Compliance:</span>
              <span class="value">{{ selectedCompliance.ComplianceItemDescription }}</span>
            </div>
            <div v-else-if="showComplianceMapping && compliances.length === 0" class="status-item">
              <span class="label">Note:</span>
              <span class="value warning">No compliance items available - saving as external risk</span>
            </div>
            <div v-else-if="showComplianceMapping" class="status-item">
              <span class="label">Note:</span>
              <span class="value">No compliance selected - will save as external risk</span>
            </div>
          </div>
        </div>

        <div class="incident-form-actions">
          <button type="button" @click="cancel" class="incident-cancel-btn">
            <i class="fas fa-times"></i> Cancel
          </button>
          
          <button
            type="submit"
            class="incident-submit-btn"
            :title="isReadyToSubmit ? `Create ${incidentType}` : 'Please fill in all required fields'"
          >
            <i class="fas fa-save"></i> Create {{ incidentType }}
          </button>
        </div>
      </form>
    </div>
    
    <!-- Popup Modal -->
    <PopupModal />
    
    <!-- Consent Modal -->
    <ConsentModal ref="consentModalRef" />
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { API_ENDPOINTS } from '../../config/api.js'
import './CreateIncident.css'
import { PopupService, PopupModal } from '@/modules/popup'
import { AccessUtils } from '@/utils/accessUtils'
import ConsentModal from '@/components/Consent/ConsentModal.vue'
import { checkConsentRequired, CONSENT_ACTIONS } from '@/utils/consentManager.js'

export default {
  name: 'CreateIncident',
  components: {
    PopupModal,
    ConsentModal
  },
  setup() {
    const router = useRouter()
    
    // Ensure framework_id is set on component mount
    onMounted(() => {
      // Ensure framework_id is set
      if (!localStorage.getItem('framework_id')) {
        const frameworkId = sessionStorage.getItem('framework_id') || 
                           localStorage.getItem('selectedFrameworkId') || 
                           '1'
        localStorage.setItem('framework_id', frameworkId)
        console.log('💡 [Consent] Set framework_id to:', frameworkId)
      }
    })
    
    const formData = ref({
      IncidentTitle: '',
      Description: '',
      Mitigation: '',
      Date: '',
      Time: '',
      Origin: '',
      Comments: '',
      RiskCategory: '',
      RiskPriority: '',
      Status: 'Open',
      AffectedBusinessUnit: '',
      SystemsAssetsInvolved: '',
      GeographicLocation: '',
      Criticality: '',
      TimelineOfEvents: '',
      InitialImpactAssessment: '',
      InternalContacts: '',
      ExternalPartiesInvolved: '',
      RegulatoryBodies: '',
      RelevantPoliciesProceduresViolated: '',
      ControlFailures: '',
      LessonsLearned: '',
      CostOfIncident: null,
      CostJustification: '',
      PossibleDamage: '',
      RepeatedNot: false,
      ReopenedNot: false,
      IncidentClassification: '',
      IncidentCategory: '',
      ComplianceId: null
    })

    // Validation errors
    const validationErrors = ref({})
    const isGeneratingAnalysis = ref(false)

    // Compliance-related reactive data
    const compliances = ref([])
    const complianceSearchTerm = ref('')
    const selectedCompliance = ref(null)
    const loadingCompliances = ref(false)
    const showDropdown = ref(false)

    // Category and Business Unit dropdown data
    const availableCategories = ref([])
    const selectedCategories = ref([])
    const categorySearchTerm = ref('')
    const showCategoryDropdown = ref(false)
    const filteredCategories = ref([])

    const availableBusinessUnits = ref([])
    const selectedBusinessUnits = ref([])
    const businessUnitSearchTerm = ref('')
    const showBusinessUnitDropdown = ref(false)
    const filteredBusinessUnits = ref([])

    // Incident Category dropdown data
    const availableIncidentCategories = ref([])
    const selectedIncidentCategories = ref([])
    const incidentCategorySearchTerm = ref('')
    const showIncidentCategoryDropdown = ref(false)
    const filteredIncidentCategories = ref([])

    // Utility function to safely truncate text
    const safeSubstring = (text, maxLength = 100) => {
      if (!text || typeof text !== 'string') {
        return ''
      }
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
    }

    // Computed properties
    const showComplianceMapping = computed(() => {
      return formData.value.IncidentClassification === 'NonConformance' || 
             formData.value.IncidentClassification === 'Control GAP'
    })

    const filteredCompliances = computed(() => {
      if (!complianceSearchTerm.value) {
        return compliances.value // Show all compliances when no search term
      }
      
      return compliances.value.filter(compliance => {
        const searchLower = complianceSearchTerm.value.toLowerCase()
        return (
          (compliance.ComplianceItemDescription && typeof compliance.ComplianceItemDescription === 'string' && compliance.ComplianceItemDescription.toLowerCase().includes(searchLower)) ||
          (compliance.Identifier && typeof compliance.Identifier === 'string' && compliance.Identifier.toLowerCase().includes(searchLower)) ||
          (compliance.SubPolicy?.Policy?.PolicyName && typeof compliance.SubPolicy.Policy.PolicyName === 'string' && compliance.SubPolicy.Policy.PolicyName.toLowerCase().includes(searchLower)) ||
          (compliance.SubPolicy?.Policy?.Framework?.FrameworkName && typeof compliance.SubPolicy.Policy.Framework.FrameworkName === 'string' && compliance.SubPolicy.Policy.Framework.FrameworkName.toLowerCase().includes(searchLower))
        )
      }) // Show all filtered results without limit
    })

    const incidentType = computed(() => {
      if (!showComplianceMapping.value) {
        return 'Regular Incident'
      }
      if (compliances.value.length === 0) {
        return 'External Risk'
      }
      if (selectedCompliance.value) {
        return 'Compliance-Linked Incident'
      }
      return 'External Risk'
    })

    const isReadyToSubmit = computed(() => {
      // Basic form validation - check required fields
      const hasRequiredFields = formData.value.IncidentTitle && 
                               formData.value.Description && 
                               formData.value.Date && 
                               formData.value.Time &&
                               formData.value.RiskPriority &&
                               selectedCategories.value.length > 0 // At least one category required
      
      // Check for validation errors
      const hasNoErrors = Object.keys(validationErrors.value).length === 0
      
      const isReady = hasRequiredFields && hasNoErrors
      
      // Only log when form is not ready to help debug
      if (!isReady) {
        console.log('=== FORM NOT READY - DEBUG INFO ===')
        console.log('Missing required fields:', {
          IncidentTitle: !formData.value.IncidentTitle,
          Description: !formData.value.Description,
          Date: !formData.value.Date,
          Time: !formData.value.Time,
          RiskPriority: !formData.value.RiskPriority,
          Categories: selectedCategories.value.length === 0
        })
        console.log('Validation errors:', validationErrors.value)
        console.log('Has required fields:', hasRequiredFields)
        console.log('Has no errors:', hasNoErrors)
      }
      
      return isReady
    })

    // Enhanced validation methods with security patterns
    const BUSINESS_TEXT_PATTERN = /^[a-zA-Z0-9\s\-_.,!?():;/\\@#$%&*+=<>[\]{}|~`"']*$/
    const ALPHANUMERIC_WITH_SPACES = /^[a-zA-Z0-9\s\-_.,!?()]*$/
    // More permissive pattern for categories
    const CATEGORY_PATTERN = /^[a-zA-Z0-9\s\-_.,!?()&]*$/

    const validateField = (value, fieldName, options = {}) => {
      const { required = false, minLength = 0, maxLength = 255, pattern = null } = options
      
      // Check if required
      if (required && (!value || value.trim() === '')) {
        return `${fieldName} is required`
      }
      
      // Skip further validation if not required and empty
      if (!required && (!value || value.trim() === '')) {
        return null
      }
      
      // Check length
      const trimmedValue = value.trim()
      if (trimmedValue.length < minLength) {
        return `${fieldName} must be at least ${minLength} characters`
      }
      
      if (trimmedValue.length > maxLength) {
        return `${fieldName} must be no more than ${maxLength} characters`
      }
      
      // Check pattern
      if (pattern && !pattern.test(trimmedValue)) {
        return `${fieldName} contains invalid characters`
      }
      
      return null
    }

    const validateCost = () => {
      const cost = formData.value.CostOfIncident
      // Cost is optional, so only validate if it has a value
      if (cost !== null && cost !== undefined && cost !== '') {
        const costNum = Number(cost)
        if (isNaN(costNum) || costNum < 0) {
          validationErrors.value.CostOfIncident = "Must be a valid positive number (e.g., 50000, 250000, 1500000)"
      } else {
          delete validationErrors.value.CostOfIncident
        }
      } else {
        // Clear any existing error if field is empty (since it's optional)
        delete validationErrors.value.CostOfIncident
      }
    }

    // Individual field validation functions
    const validateIncidentTitle = () => {
      const titleError = validateField(formData.value.IncidentTitle, 'Incident Title', {
        required: true,
        minLength: 3,
        maxLength: 255,
        pattern: BUSINESS_TEXT_PATTERN
      })
      if (titleError) {
        validationErrors.value.IncidentTitle = titleError
      } else {
        delete validationErrors.value.IncidentTitle
      }
    }

    const validateDescription = () => {
      const descError = validateField(formData.value.Description, 'Description', {
        required: true,
        minLength: 10,
        maxLength: 2000,
        pattern: BUSINESS_TEXT_PATTERN
      })
      if (descError) {
        validationErrors.value.Description = descError
      } else {
        delete validationErrors.value.Description
      }
    }

    const validateOrigin = () => {
      const allowedOrigins = ['Manual', 'System Generated']
      // Origin is optional, so only validate if it has a value
      if (formData.value.Origin) {
        if (!allowedOrigins.includes(formData.value.Origin)) {
          validationErrors.value.Origin = 'Must be one of: Manual, System Generated'
        } else {
          delete validationErrors.value.Origin
        }
      } else {
        // Clear any existing error if field is empty (since it's optional)
        delete validationErrors.value.Origin
      }
    }

    const validateDate = () => {
      if (!formData.value.Date) {
        validationErrors.value.Date = "Date is required"
      } else {
        delete validationErrors.value.Date
      }
    }
    
    const validateTime = () => {
      if (!formData.value.Time) {
        validationErrors.value.Time = "Time is required"
      } else {
        delete validationErrors.value.Time
      }
    }
    
    const validateRiskPriority = () => {
      const allowedPriorities = ['High', 'Medium', 'Low']
      if (!formData.value.RiskPriority) {
        validationErrors.value.RiskPriority = "Risk priority is required"
      } else if (!allowedPriorities.includes(formData.value.RiskPriority)) {
        validationErrors.value.RiskPriority = 'Must be one of: High, Medium, Low'
      } else {
        delete validationErrors.value.RiskPriority
      }
    }

    const validateRiskCategory = () => {
      // For multi-select, check if at least one category is selected
      if (selectedCategories.value.length === 0) {
        validationErrors.value.RiskCategory = 'At least one risk category is required'
      } else {
        // Validate each selected category
        const invalidCategories = selectedCategories.value.filter(category => {
          const isValid = category && category.length <= 100 && CATEGORY_PATTERN.test(category)
          return !isValid
        })
        
        if (invalidCategories.length > 0) {
          validationErrors.value.RiskCategory = 'One or more categories contain invalid characters or are too long'
        } else {
          delete validationErrors.value.RiskCategory
        }
      }
    }

    const validateCriticality = () => {
      const allowedCriticality = ['Critical', 'High', 'Medium', 'Low']
      if (formData.value.Criticality && !allowedCriticality.includes(formData.value.Criticality)) {
        validationErrors.value.Criticality = 'Must be one of: Critical, High, Medium, Low'
      } else {
        delete validationErrors.value.Criticality
      }
    }

    const validatePossibleDamage = () => {
      const damageError = validateField(formData.value.PossibleDamage, 'Possible Damage', {
        maxLength: 1000,
        pattern: BUSINESS_TEXT_PATTERN
      })
      if (damageError) {
        validationErrors.value.PossibleDamage = damageError
      } else {
        delete validationErrors.value.PossibleDamage
      }
    }

    const validateBusinessUnit = () => {
      // Business units are optional, so only validate if some are selected
      if (selectedBusinessUnits.value.length > 0) {
        // Validate each selected business unit
        const invalidUnits = selectedBusinessUnits.value.filter(unit => {
          return !unit || unit.length > 100 || !ALPHANUMERIC_WITH_SPACES.test(unit)
        })
        
        if (invalidUnits.length > 0) {
          validationErrors.value.AffectedBusinessUnit = 'One or more business units contain invalid characters or are too long'
        } else {
          delete validationErrors.value.AffectedBusinessUnit
        }
      } else {
        delete validationErrors.value.AffectedBusinessUnit
      }
    }

    const validateGeographicLocation = () => {
      const locationError = validateField(formData.value.GeographicLocation, 'Geographic Location', {
        maxLength: 100,
        pattern: ALPHANUMERIC_WITH_SPACES
      })
      if (locationError) {
        validationErrors.value.GeographicLocation = locationError
      } else {
        delete validationErrors.value.GeographicLocation
      }
    }

    const validateSystemsInvolved = () => {
      const systemsError = validateField(formData.value.SystemsAssetsInvolved, 'Systems Involved', {
        maxLength: 500,
        pattern: BUSINESS_TEXT_PATTERN
      })
      if (systemsError) {
        validationErrors.value.SystemsAssetsInvolved = systemsError
      } else {
        delete validationErrors.value.SystemsAssetsInvolved
      }
    }

    const validateInitialImpact = () => {
      const impactError = validateField(formData.value.InitialImpactAssessment, 'Initial Impact Assessment', {
        maxLength: 2000,
        pattern: BUSINESS_TEXT_PATTERN
      })
      if (impactError) {
        validationErrors.value.InitialImpactAssessment = impactError
      } else {
        delete validationErrors.value.InitialImpactAssessment
      }
    }

    const validateMitigation = () => {
      const mitigationError = validateField(formData.value.Mitigation, 'Mitigation Steps', {
        maxLength: 2000,
        pattern: BUSINESS_TEXT_PATTERN
      })
      if (mitigationError) {
        validationErrors.value.Mitigation = mitigationError
      } else {
        delete validationErrors.value.Mitigation
      }
    }

    const validateComments = () => {
      const commentsError = validateField(formData.value.Comments, 'Comments', {
        maxLength: 1000,
        pattern: BUSINESS_TEXT_PATTERN
      })
      if (commentsError) {
        validationErrors.value.Comments = commentsError
      } else {
        delete validationErrors.value.Comments
      }
    }

    const validateInternalContacts = () => {
      const contactsError = validateField(formData.value.InternalContacts, 'Internal Contacts', {
        maxLength: 500,
        pattern: BUSINESS_TEXT_PATTERN
      })
      if (contactsError) {
        validationErrors.value.InternalContacts = contactsError
      } else {
        delete validationErrors.value.InternalContacts
      }
    }

    const validateExternalParties = () => {
      const partiesError = validateField(formData.value.ExternalPartiesInvolved, 'External Parties', {
        maxLength: 500,
        pattern: BUSINESS_TEXT_PATTERN
      })
      if (partiesError) {
        validationErrors.value.ExternalPartiesInvolved = partiesError
      } else {
        delete validationErrors.value.ExternalPartiesInvolved
      }
    }

    const validateRegulatoryBodies = () => {
      const bodiesError = validateField(formData.value.RegulatoryBodies, 'Regulatory Bodies', {
        maxLength: 500,
        pattern: BUSINESS_TEXT_PATTERN
      })
      if (bodiesError) {
        validationErrors.value.RegulatoryBodies = bodiesError
      } else {
        delete validationErrors.value.RegulatoryBodies
      }
    }

    const validateViolatedPolicies = () => {
      const policiesError = validateField(formData.value.RelevantPoliciesProceduresViolated, 'Violated Policies/Procedures', {
        maxLength: 1000,
        pattern: BUSINESS_TEXT_PATTERN
      })
      if (policiesError) {
        validationErrors.value.RelevantPoliciesProceduresViolated = policiesError
      } else {
        delete validationErrors.value.RelevantPoliciesProceduresViolated
      }
    }

    const validateControlFailures = () => {
      const failuresError = validateField(formData.value.ControlFailures, 'Control Failures', {
        maxLength: 1000,
        pattern: BUSINESS_TEXT_PATTERN
      })
      if (failuresError) {
        validationErrors.value.ControlFailures = failuresError
      } else {
        delete validationErrors.value.ControlFailures
      }
    }

    const validateIncidentCategory = () => {
      // Incident categories are optional, so only validate if some are selected
      if (selectedIncidentCategories.value.length > 0) {
        // Validate each selected incident category
        const invalidCategories = selectedIncidentCategories.value.filter(category => {
          return !category || category.length > 100 || !CATEGORY_PATTERN.test(category)
        })
        
        if (invalidCategories.length > 0) {
          validationErrors.value.IncidentCategory = 'One or more incident categories contain invalid characters or are too long'
        } else {
          delete validationErrors.value.IncidentCategory
        }
      } else {
        delete validationErrors.value.IncidentCategory
      }
    }

    const validateForm = () => {
      // Reset validation errors
      validationErrors.value = {}
      
      // Required fields (actual form fields)
      const requiredFields = [
        'IncidentTitle', 'Description', 'Origin', 'Date', 'Time', 'RiskPriority'
      ]
      
      let isValid = true
      
      // Check required fields
      for (const field of requiredFields) {
        if (!formData.value[field] || (typeof formData.value[field] === 'string' && !formData.value[field].trim())) {
          validationErrors.value[field] = `${field.replace(/([A-Z])/g, ' $1').trim()} is required`
          isValid = false
        }
      }
      // Check at least one risk category selected
      if (selectedCategories.value.length === 0) {
        validationErrors.value.RiskCategory = 'At least one risk category is required'
        isValid = false
      }
      
      return isValid
    }
    
    // Function to show validation summary in console
    const showValidationSummary = () => {
      console.log('Validation errors:', validationErrors.value)
      
      // Log each error with field name
      Object.entries(validationErrors.value).forEach(([field, error]) => {
        console.log(`${field}: ${error}`)
      })
    }

    // Methods
    const fetchCompliances = async () => {
      if (compliances.value.length > 0) return // Already loaded

      loadingCompliances.value = true
      try {
        const response = await axios.get(API_ENDPOINTS.INCIDENT_COMPLIANCES)
        if (response.data.success) {
          compliances.value = response.data.data
          console.log('Loaded compliances:', compliances.value.length)
          
          // Debug: Check for any compliance items with invalid data types
          const invalidCompliances = compliances.value.filter(compliance => {
            return (compliance.Mitigation && typeof compliance.Mitigation !== 'string') ||
                   (compliance.PossibleDamage && typeof compliance.PossibleDamage !== 'string') ||
                   (compliance.ComplianceItemDescription && typeof compliance.ComplianceItemDescription !== 'string')
          })
          
          if (invalidCompliances.length > 0) {
            console.warn('Found compliances with invalid data types:', invalidCompliances)
          }
        } else {
          console.error('Failed to fetch compliances:', response.data.message)
        }
      } catch (error) {
        console.error('Error fetching compliances:', error)
        
        // Check if this is an access denied error first
        if (!AccessUtils.handleApiError(error, 'view compliances')) {
          // Only show generic error if it's not an access denied error
          PopupService.error('Failed to load compliances. Please try again.')
        }
      } finally {
        loadingCompliances.value = false
      }
    }

    const onClassificationChange = () => {
      // Clear compliance selection when classification changes
      if (!showComplianceMapping.value) {
        formData.value.ComplianceId = null
        selectedCompliance.value = null
        complianceSearchTerm.value = ''
        showDropdown.value = false
      } else {
        // Load compliances when needed
        fetchCompliances()
        showDropdown.value = false // Start with dropdown closed
      }
    }

    const selectCompliance = (compliance) => {
      formData.value.ComplianceId = compliance.ComplianceId
      selectedCompliance.value = compliance
      complianceSearchTerm.value = '' // Clear search term
      showDropdown.value = false // Close dropdown
      
      // Auto-fill some fields from compliance if they're empty
      if (!formData.value.PossibleDamage && compliance.PossibleDamage && typeof compliance.PossibleDamage === 'string') {
        formData.value.PossibleDamage = compliance.PossibleDamage
      }
      if (!formData.value.Mitigation && compliance.Mitigation && typeof compliance.Mitigation === 'string') {
        formData.value.Mitigation = compliance.Mitigation
      }
      if (!formData.value.Criticality && compliance.Criticality && typeof compliance.Criticality === 'string') {
        formData.value.Criticality = compliance.Criticality
      }
      
      console.log('Selected compliance:', compliance.ComplianceId, compliance.ComplianceItemDescription)
      console.log('Dropdown closed after selection')
    }

    const clearCompliance = () => {
      formData.value.ComplianceId = null
      selectedCompliance.value = null
      complianceSearchTerm.value = ''
      showDropdown.value = false
      console.log('Compliance selection cleared')
    }

    const filterCompliances = () => {
      // Show dropdown when user starts typing
      if (complianceSearchTerm.value.length > 0) {
        showDropdown.value = true
      }
    }

    const hideDropdownDelayed = () => {
      // Add a small delay to allow click events on dropdown items to fire first
      setTimeout(() => {
        showDropdown.value = false
      }, 150)
    }

    const validateAndSubmit = async () => {
      console.log('=== SUBMIT ATTEMPT ===')
      
      if (!validateForm()) {
        console.log('Form validation failed')
        showValidationSummary()
        PopupService.error('Please correct the validation errors before submitting. Check the console for details.')
        return
      }
      
      console.log('Form validation passed, submitting...')
      await submitForm()
    }

    const consentModalRef = ref(null)
    const showConsentModal = ref(false)
    const consentConfig = ref(null)

    const submitForm = async () => {
      let consentRequired = false
      let consentConfigData = null
      
      try {
        // Check if consent is required from database
        console.log('🔍 [Consent] Checking consent requirement for create_incident')
        console.log('🔍 [Consent] Framework ID in localStorage:', localStorage.getItem('framework_id'))
        console.log('🔍 [Consent] User ID in localStorage:', localStorage.getItem('user_id'))
        
        const consentCheck = await checkConsentRequired(CONSENT_ACTIONS.CREATE_INCIDENT)
        console.log('🔍 [Consent] Consent check result:', consentCheck)
        
        consentRequired = consentCheck.required
        consentConfigData = consentCheck.config
        
        console.log('🔍 [Consent] consentRequired:', consentRequired)
        console.log('🔍 [Consent] consentConfigData:', consentConfigData)
        
        // If consent is required, show modal
        if (consentRequired && consentConfigData) {
          console.log('✅ [Consent] Consent required, showing modal')
          console.log('✅ [Consent] Config details:', {
            config_id: consentConfigData.config_id,
            action_type: consentConfigData.action_type,
            action_label: consentConfigData.action_label,
            is_enabled: consentConfigData.is_enabled
          })
          
          consentConfig.value = consentConfigData
          showConsentModal.value = true
          
          // Wait a bit for the modal to render
          await new Promise(resolve => setTimeout(resolve, 100))
          
          if (!consentModalRef.value) {
            console.error('❌ [Consent] ConsentModal ref is null! Modal may not be rendered.')
            PopupService.error('Error: Consent modal could not be displayed. Please refresh the page.')
            showConsentModal.value = false
          return
          }
          
          try {
            console.log('✅ [Consent] Calling consentModalRef.value.show()')
            const accepted = await consentModalRef.value.show(CONSENT_ACTIONS.CREATE_INCIDENT, consentConfigData)
            console.log('✅ [Consent] Modal show() returned:', accepted)
            
            if (!accepted) {
              console.log('❌ [Consent] User declined consent')
              showConsentModal.value = false
              PopupService.warning('Incident creation cancelled - consent is required')
              return
            }
            
            console.log('✅ [Consent] User accepted consent')
            showConsentModal.value = false
          } catch (error) {
            console.error('❌ [Consent] Error showing consent modal:', error)
            console.log('❌ [Consent] User cancelled consent modal')
            showConsentModal.value = false
            return
          }
        } else {
          if (!consentRequired) {
            console.log('ℹ️ [Consent] Consent not required - is_enabled is false or config not found')
          } else if (!consentConfigData) {
            console.warn('⚠️ [Consent] Consent required but config is null!')
          }
        }
        
        // Prepare form data - include ComplianceId only if a compliance is selected
        const submissionData = { ...formData.value }
        
        // Add consent data if consent was required and accepted
        if (consentRequired && consentConfigData && consentConfig.value) {
          submissionData.consent_accepted = true
          submissionData.consent_config_id = consentConfig.value.config_id
          submissionData.framework_id = localStorage.getItem('framework_id')
          console.log('📋 [Consent] Including consent data in request:', {
            consent_accepted: true,
            consent_config_id: consentConfig.value.config_id
          })
        }
        
        // Ensure ComplianceId is null if no compliance is selected
        if (!selectedCompliance.value || !formData.value.ComplianceId) {
          submissionData.ComplianceId = null
          console.log('No compliance selected - saving as external risk')
        } else {
          console.log('Compliance selected:', selectedCompliance.value.ComplianceItemDescription)
        }
        
        console.log('Submitting incident with data:', submissionData)
        
        const response = await axios.post(API_ENDPOINTS.INCIDENT_CREATE, submissionData)
        if (response.status === 201) {
          // Show success message and redirect
          PopupService.success('Incident created successfully! It has been saved to the incidents table and will be escalated to risk management when needed.')
          
          // Navigate to incidents list after a short delay to allow user to see success message
          setTimeout(() => {
            router.push('/incident/incident')
          }, 2000) // 2 second delay to show the success message
        }
      } catch (error) {
        console.error('Error creating incident:', error)
        
        // Check if this is an access denied error first
        if (!AccessUtils.handleApiError(error, 'create incidents')) {
          // Only show generic error if it's not an access denied error
          if (error.response && error.response.data) {
            // Handle validation errors from server
            const serverErrors = error.response.data
            Object.keys(serverErrors).forEach(field => {
              validationErrors.value[field] = Array.isArray(serverErrors[field]) 
                ? serverErrors[field][0] 
                : serverErrors[field]
            })
            PopupService.error('Please correct the validation errors and try again.')
          } else {
            PopupService.error('Error creating incident. Please try again.')
          }
        }
      }
    }

    const cancel = () => {
      // Navigate back to incidents list
      router.push('/incident/incident')
    }

    const generateAnalysis = async () => {
      // Validate that we have title and description
      if (!formData.value.IncidentTitle || !formData.value.Description) {
        PopupService.error('Please enter both incident title and description before generating analysis.')
        return
      }

      if (formData.value.IncidentTitle.trim().length < 3) {
        PopupService.error('Incident title must be at least 3 characters long.')
        return
      }

      if (formData.value.Description.trim().length < 10) {
        PopupService.error('Incident description must be at least 10 characters long.')
        return
      }

      isGeneratingAnalysis.value = true

      try {
        PopupService.info('Generating analysis... This may take a few moments.')
        
        // Call the analysis API without timeout
        const response = await axios.post('api/incidents/generate-analysis/', {
          title: formData.value.IncidentTitle.trim(),
          description: formData.value.Description.trim()
        })

        if (response.data.success && response.data.analysis) {
          const analysis = response.data.analysis
          console.log('Analysis received:', analysis)
          
          // Debug: Log the structure of key fields
          console.log('possibleDamage type:', typeof analysis.possibleDamage, 'value:', analysis.possibleDamage)
          console.log('initialImpactAssessment type:', typeof analysis.initialImpactAssessment, 'value:', analysis.initialImpactAssessment)
          console.log('mitigationSteps type:', typeof analysis.mitigationSteps, 'value:', analysis.mitigationSteps)
          console.log('systemsInvolved type:', typeof analysis.systemsInvolved, 'value:', analysis.systemsInvolved)

          // Map the analysis results to form fields
          if (analysis.riskPriority) {
            // Map P0/P1/P2/P3 to High/Medium/Low priority system
            const priorityMap = {
              'P0': 'High',
              'P1': 'High', 
              'P2': 'Medium',
              'P3': 'Low'
            }
            formData.value.RiskPriority = priorityMap[analysis.riskPriority] || analysis.riskPriority
          }

          if (analysis.criticality) {
            formData.value.Criticality = analysis.criticality
          }

          if (analysis.costOfIncident) {
            // Ensure it's a number
            formData.value.CostOfIncident = typeof analysis.costOfIncident === 'number' 
              ? analysis.costOfIncident 
              : parseInt(analysis.costOfIncident) || 0
          }

          if (analysis.costJustification) {
            formData.value.CostJustification = analysis.costJustification
          }

          // Handle possibleDamage - could be string or object
          if (analysis.possibleDamage) {
            if (typeof analysis.possibleDamage === 'string') {
              formData.value.PossibleDamage = analysis.possibleDamage
            } else if (typeof analysis.possibleDamage === 'object') {
              // Convert object to formatted string
              const damageEntries = Object.entries(analysis.possibleDamage)
                .map(([key, value]) => `${key}: ${value}`)
                .join('\n')
              formData.value.PossibleDamage = damageEntries
            }
          }

          // Handle systemsInvolved - could be array or string
          if (analysis.systemsInvolved) {
            if (Array.isArray(analysis.systemsInvolved)) {
              formData.value.SystemsAssetsInvolved = analysis.systemsInvolved.join(', ')
            } else if (typeof analysis.systemsInvolved === 'string') {
              formData.value.SystemsAssetsInvolved = analysis.systemsInvolved
            }
          }

          // Handle initialImpactAssessment - could be string or object
          if (analysis.initialImpactAssessment) {
            if (typeof analysis.initialImpactAssessment === 'string') {
              formData.value.InitialImpactAssessment = analysis.initialImpactAssessment
            } else if (typeof analysis.initialImpactAssessment === 'object') {
              // Convert object to formatted string
              const impactEntries = Object.entries(analysis.initialImpactAssessment)
                .map(([key, value]) => `${key}: ${value}`)
                .join('\n')
              formData.value.InitialImpactAssessment = impactEntries
            }
          }

          // Handle mitigationSteps - could be array or object
          if (analysis.mitigationSteps) {
            if (Array.isArray(analysis.mitigationSteps)) {
              formData.value.Mitigation = analysis.mitigationSteps.join('\n')
            } else if (typeof analysis.mitigationSteps === 'object') {
              // Convert object to formatted string
              const mitigationEntries = Object.entries(analysis.mitigationSteps)
                .map(([key, value]) => `${key}: ${value}`)
                .join('\n')
              formData.value.Mitigation = mitigationEntries
            }
          }

          if (analysis.comments) {
            formData.value.Comments = analysis.comments
          }

          // Handle violatedPolicies - could be array or string
          if (analysis.violatedPolicies) {
            if (Array.isArray(analysis.violatedPolicies)) {
              formData.value.RelevantPoliciesProceduresViolated = analysis.violatedPolicies.join('\n')
            } else if (typeof analysis.violatedPolicies === 'string') {
              formData.value.RelevantPoliciesProceduresViolated = analysis.violatedPolicies
            }
          }

          // Handle procedureControlFailures - could be array or string
          if (analysis.procedureControlFailures) {
            if (Array.isArray(analysis.procedureControlFailures)) {
              formData.value.ControlFailures = analysis.procedureControlFailures.join('\n')
            } else if (typeof analysis.procedureControlFailures === 'string') {
              formData.value.ControlFailures = analysis.procedureControlFailures
            }
          }

          // Handle lessonsLearned - could be array or string
          if (analysis.lessonsLearned) {
            if (Array.isArray(analysis.lessonsLearned)) {
              formData.value.LessonsLearned = analysis.lessonsLearned.join('\n')
            } else if (typeof analysis.lessonsLearned === 'string') {
              formData.value.LessonsLearned = analysis.lessonsLearned
            }
          }

          // Handle risk categories - try to extract categories from the analysis
          if (analysis.riskCategory || analysis.category) {
            const categoryText = analysis.riskCategory || analysis.category
            // Clear existing categories and add the new one
            selectedCategories.value = []
            
            if (typeof categoryText === 'string') {
              // Split by common delimiters and clean up
              const categories = categoryText.split(/[,;|&]/).map(cat => cat.trim()).filter(cat => cat.length > 0)
              
              for (const category of categories) {
                // Add to available categories if not exists
                if (!availableCategories.value.some(cat => cat.toLowerCase() === category.toLowerCase())) {
                  availableCategories.value.push(category)
                }
                
                // Add to selected categories
                if (!selectedCategories.value.includes(category)) {
                  selectedCategories.value.push(category)
                }
              }
              
              updateFormDataCategories()
            }
          }

          // Debug: Log the final form values after processing
          console.log('Final form values after analysis:')
          console.log('PossibleDamage:', formData.value.PossibleDamage)
          console.log('InitialImpactAssessment:', formData.value.InitialImpactAssessment)
          console.log('Mitigation:', formData.value.Mitigation)
          console.log('SystemsAssetsInvolved:', formData.value.SystemsAssetsInvolved)
          console.log('RelevantPoliciesProceduresViolated:', formData.value.RelevantPoliciesProceduresViolated)
          console.log('ControlFailures:', formData.value.ControlFailures)
          console.log('LessonsLearned:', formData.value.LessonsLearned)

          // Clear any validation errors for fields that were populated
          Object.keys(validationErrors.value).forEach(field => {
            if (formData.value[field] && formData.value[field].toString().trim()) {
              delete validationErrors.value[field]
            }
          })

          PopupService.success('Analysis completed! Form fields have been populated with AI-generated insights. Please review and modify as needed before saving.')
          
        } else {
          throw new Error(response.data.error || 'Analysis failed')
        }

      } catch (error) {
        console.error('Error generating analysis:', error)
        
        // Check if this is an access denied error first
        if (!AccessUtils.handleApiError(error, 'generate incident analysis')) {
          // Only show generic error if it's not an access denied error
          let errorMessage = 'Failed to generate analysis. '
          
          if (error.code === 'ECONNABORTED') {
            errorMessage += 'Request timed out. The server took too long to respond. Please try again or fill the form manually.'
          } else if (error.response && error.response.data && error.response.data.error) {
            errorMessage += error.response.data.error
          } else if (error.message) {
            errorMessage += error.message
          } else {
            errorMessage += 'Please try again or fill the form manually.'
          }
          
          PopupService.error(errorMessage)
        }
      } finally {
        isGeneratingAnalysis.value = false
      }
    }
    // Category dropdown methods
    const fetchCategories = async () => {
      try {
        const response = await axios.get(API_ENDPOINTS.CATEGORIES)
        availableCategories.value = response.data
        filteredCategories.value = response.data
      } catch (error) {
        console.error('Error fetching categories:', error)
        
        // Check if this is an access denied error first
        if (!AccessUtils.handleApiError(error, 'view categories')) {
          // Only show generic error if it's not an access denied error
          PopupService.error('Failed to load categories. Please try again.')
        }
      }
    }

    const toggleCategoryDropdown = () => {
      showCategoryDropdown.value = !showCategoryDropdown.value
      if (showCategoryDropdown.value) {
        filteredCategories.value = availableCategories.value
      }
    }

    const filterCategories = () => {
      const searchTerm = categorySearchTerm.value.toLowerCase()
      filteredCategories.value = availableCategories.value.filter(category =>
        category.toLowerCase().includes(searchTerm)
      )
    }

    const toggleCategory = (category) => {
      if (selectedCategories.value.includes(category)) {
        selectedCategories.value = selectedCategories.value.filter(c => c !== category)
      } else {
        selectedCategories.value.push(category)
      }
      updateFormDataCategories()
    }

    const removeCategory = (category) => {
      selectedCategories.value = selectedCategories.value.filter(c => c !== category)
      updateFormDataCategories()
    }

    const addCustomCategory = async () => {
      const newCategory = categorySearchTerm.value.trim()
      console.log('Adding custom category:', newCategory)
      
      if (newCategory && !availableCategories.value.some(cat => cat.toLowerCase() === newCategory.toLowerCase())) {
        try {
          console.log('Posting new category to API:', newCategory)
          const response = await axios.post(API_ENDPOINTS.CATEGORIES_ADD, { value: newCategory })
          console.log('API response:', response.data)
          
          const addedCategory = response.data.value || newCategory
          
          // Add to available categories if not already there
          if (!availableCategories.value.includes(addedCategory)) {
            availableCategories.value.push(addedCategory)
            console.log('Added to available categories:', addedCategory)
          }
          
          // Add to selected categories if not already selected
          if (!selectedCategories.value.includes(addedCategory)) {
            selectedCategories.value.push(addedCategory)
            console.log('Added to selected categories:', addedCategory)
          }
          
          // Clear search and update filtered list
          categorySearchTerm.value = ''
          filteredCategories.value = availableCategories.value
          
          // Update form data and trigger validation
          updateFormDataCategories()
          
          // Force clear any lingering category validation errors
          setTimeout(() => {
            if (selectedCategories.value.length > 0) {
              delete validationErrors.value.RiskCategory
              console.log('Force cleared RiskCategory validation error')
            }
          }, 100)
          
          PopupService.success(`Category "${addedCategory}" added successfully!`)
        } catch (error) {
          console.error('Error adding category:', error)
          
          // Check if this is an access denied error first
          if (!AccessUtils.handleApiError(error, 'add categories')) {
            // Only show generic error if it's not an access denied error
            PopupService.error('Failed to add category. Please try again.')
          }
        }
      } else if (newCategory && availableCategories.value.some(cat => cat.toLowerCase() === newCategory.toLowerCase())) {
        // Category exists, just select it
        const existingCategory = availableCategories.value.find(cat => cat.toLowerCase() === newCategory.toLowerCase())
        console.log('Category already exists, selecting:', existingCategory)
        
        if (!selectedCategories.value.includes(existingCategory)) {
          selectedCategories.value.push(existingCategory)
          updateFormDataCategories()
        }
        categorySearchTerm.value = ''
      } else if (!newCategory) {
        console.log('Empty category name provided')
      } else {
        console.log('Category already selected:', newCategory)
      }
    }

    const updateFormDataCategories = () => {
      formData.value.RiskCategory = selectedCategories.value.join(', ')
      validateRiskCategory() // Trigger validation when categories change
    }

    // Business Unit dropdown methods
    const fetchBusinessUnits = async () => {
      try {
        const response = await axios.get(API_ENDPOINTS.BUSINESS_UNITS)
        availableBusinessUnits.value = response.data
        filteredBusinessUnits.value = response.data
      } catch (error) {
        console.error('Error fetching business units:', error)
        
        // Check if this is an access denied error first
        if (!AccessUtils.handleApiError(error, 'view business units')) {
          // Only show generic error if it's not an access denied error
          PopupService.error('Failed to load business units. Please try again.')
        }
      }
    }

    const toggleBusinessUnitDropdown = () => {
      showBusinessUnitDropdown.value = !showBusinessUnitDropdown.value
      if (showBusinessUnitDropdown.value) {
        filteredBusinessUnits.value = availableBusinessUnits.value
      }
    }

    const filterBusinessUnits = () => {
      const searchTerm = businessUnitSearchTerm.value.toLowerCase()
      filteredBusinessUnits.value = availableBusinessUnits.value.filter(unit =>
        unit.toLowerCase().includes(searchTerm)
      )
    }

    const toggleBusinessUnit = (unit) => {
      if (selectedBusinessUnits.value.includes(unit)) {
        selectedBusinessUnits.value = selectedBusinessUnits.value.filter(u => u !== unit)
      } else {
        selectedBusinessUnits.value.push(unit)
      }
      updateFormDataBusinessUnits()
    }

    const removeBusinessUnit = (unit) => {
      selectedBusinessUnits.value = selectedBusinessUnits.value.filter(u => u !== unit)
      updateFormDataBusinessUnits()
    }

    const addCustomBusinessUnit = async () => {
      const newUnit = businessUnitSearchTerm.value.trim()
      console.log('Adding custom business unit:', newUnit)
      
      if (newUnit && !availableBusinessUnits.value.some(unit => unit.toLowerCase() === newUnit.toLowerCase())) {
        try {
          console.log('Posting new business unit to API:', newUnit)
          const response = await axios.post(API_ENDPOINTS.BUSINESS_UNITS_ADD, { value: newUnit })
          console.log('API response:', response.data)
          
          const addedUnit = response.data.value || newUnit
          
          // Add to available business units if not already there
          if (!availableBusinessUnits.value.includes(addedUnit)) {
            availableBusinessUnits.value.push(addedUnit)
            console.log('Added to available business units:', addedUnit)
          }
          
          // Add to selected business units if not already selected
          if (!selectedBusinessUnits.value.includes(addedUnit)) {
            selectedBusinessUnits.value.push(addedUnit)
            console.log('Added to selected business units:', addedUnit)
          }
          
          // Clear search and update filtered list
          businessUnitSearchTerm.value = ''
          filteredBusinessUnits.value = availableBusinessUnits.value
          
          // Update form data and trigger validation
          updateFormDataBusinessUnits()
          
          // Force clear any lingering business unit validation errors
          setTimeout(() => {
            delete validationErrors.value.AffectedBusinessUnit
            console.log('Force cleared AffectedBusinessUnit validation error')
          }, 100)
          
          PopupService.success(`Business unit "${addedUnit}" added successfully!`)
        } catch (error) {
          console.error('Error adding business unit:', error)
          
          // Check if this is an access denied error first
          if (!AccessUtils.handleApiError(error, 'add business units')) {
            // Only show generic error if it's not an access denied error
            PopupService.error('Failed to add business unit. Please try again.')
          }
        }
      } else if (newUnit && availableBusinessUnits.value.some(unit => unit.toLowerCase() === newUnit.toLowerCase())) {
        // Business unit exists, just select it
        const existingUnit = availableBusinessUnits.value.find(unit => unit.toLowerCase() === newUnit.toLowerCase())
        console.log('Business unit already exists, selecting:', existingUnit)
        
        if (!selectedBusinessUnits.value.includes(existingUnit)) {
          selectedBusinessUnits.value.push(existingUnit)
          updateFormDataBusinessUnits()
        }
        businessUnitSearchTerm.value = ''
      } else if (!newUnit) {
        console.log('Empty business unit name provided')
      } else {
        console.log('Business unit already selected:', newUnit)
      }
    }

    const updateFormDataBusinessUnits = () => {
      formData.value.AffectedBusinessUnit = selectedBusinessUnits.value.join(', ')
      validateBusinessUnit() // Trigger validation when business units change
    }

    // Incident Category dropdown methods
    const fetchIncidentCategories = async () => {
      try {
        // Use the dedicated incident categories endpoint
        const response = await axios.get(API_ENDPOINTS.INCIDENT_CATEGORIES)
        
        // Default incident categories if none exist
        const defaultIncidentCategories = [
          'Security Incident',
          'Data Breach',
          'System Outage',
          'Operational Failure',
          'Compliance Violation',
          'Privacy Incident',
          'Network Incident',
          'Application Error',
          'Infrastructure Failure',
          'Human Error',
          'External Attack',
          'Internal Threat',
          'Business Disruption',
          'Service Degradation',
          'Configuration Error'
        ]
        
        // The response should be an array of categories
        const existingCategories = Array.isArray(response.data) ? response.data : []
        const combinedCategories = [...new Set([...existingCategories, ...defaultIncidentCategories])]
        
        availableIncidentCategories.value = combinedCategories
        filteredIncidentCategories.value = combinedCategories
      } catch (error) {
        console.error('Error fetching incident categories:', error)
        
        // Use default categories if API fails
        const defaultIncidentCategories = [
          'Security Incident',
          'Data Breach', 
          'System Outage',
          'Operational Failure',
          'Compliance Violation',
          'Privacy Incident',
          'Network Incident',
          'Application Error',
          'Infrastructure Failure',
          'Human Error',
          'External Attack',
          'Internal Threat',
          'Business Disruption',
          'Service Degradation',
          'Configuration Error'
        ]
        
        availableIncidentCategories.value = defaultIncidentCategories
        filteredIncidentCategories.value = defaultIncidentCategories
        
        if (!AccessUtils.handleApiError(error, 'view incident categories')) {
          PopupService.warning('Using default incident categories. Failed to load custom categories.')
        }
      }
    }

    const toggleIncidentCategoryDropdown = () => {
      showIncidentCategoryDropdown.value = !showIncidentCategoryDropdown.value
      if (showIncidentCategoryDropdown.value) {
        filteredIncidentCategories.value = availableIncidentCategories.value
      }
    }

    const filterIncidentCategories = () => {
      const searchTerm = incidentCategorySearchTerm.value.toLowerCase()
      filteredIncidentCategories.value = availableIncidentCategories.value.filter(category =>
        category.toLowerCase().includes(searchTerm)
      )
    }

    const toggleIncidentCategory = (category) => {
      if (selectedIncidentCategories.value.includes(category)) {
        selectedIncidentCategories.value = selectedIncidentCategories.value.filter(c => c !== category)
      } else {
        selectedIncidentCategories.value.push(category)
      }
      updateFormDataIncidentCategories()
    }

    const removeIncidentCategory = (category) => {
      selectedIncidentCategories.value = selectedIncidentCategories.value.filter(c => c !== category)
      updateFormDataIncidentCategories()
    }

    const addCustomIncidentCategory = async () => {
      const newCategory = incidentCategorySearchTerm.value.trim()
      console.log('Adding custom incident category:', newCategory)
      
      if (newCategory && !availableIncidentCategories.value.some(cat => cat.toLowerCase() === newCategory.toLowerCase())) {
        try {
          console.log('Posting new incident category to API:', newCategory)
          const response = await axios.post(API_ENDPOINTS.INCIDENT_CATEGORIES_ADD, { value: newCategory })
          console.log('API response:', response.data)
          
          const addedCategory = response.data.value || newCategory
          
          // Add to available incident categories if not already there
          if (!availableIncidentCategories.value.includes(addedCategory)) {
            availableIncidentCategories.value.push(addedCategory)
            console.log('Added to available incident categories:', addedCategory)
          }
          
          // Add to selected incident categories if not already selected
          if (!selectedIncidentCategories.value.includes(addedCategory)) {
            selectedIncidentCategories.value.push(addedCategory)
            console.log('Added to selected incident categories:', addedCategory)
          }
          
          // Clear search and update filtered list
          incidentCategorySearchTerm.value = ''
          filteredIncidentCategories.value = availableIncidentCategories.value
          
          // Update form data and trigger validation
          updateFormDataIncidentCategories()
          
          // Force clear any lingering incident category validation errors
          setTimeout(() => {
            if (selectedIncidentCategories.value.length > 0) {
              delete validationErrors.value.IncidentCategory
              console.log('Force cleared IncidentCategory validation error')
            }
          }, 100)
          
          PopupService.success(`Incident category "${addedCategory}" added successfully!`)
        } catch (error) {
          console.error('Error adding incident category:', error)
          
          if (!AccessUtils.handleApiError(error, 'add incident categories')) {
            PopupService.error('Failed to add incident category. Please try again.')
          }
        }
      } else if (newCategory && availableIncidentCategories.value.some(cat => cat.toLowerCase() === newCategory.toLowerCase())) {
        // Category exists, just select it
        const existingCategory = availableIncidentCategories.value.find(cat => cat.toLowerCase() === newCategory.toLowerCase())
        console.log('Incident category already exists, selecting:', existingCategory)
        
        if (!selectedIncidentCategories.value.includes(existingCategory)) {
          selectedIncidentCategories.value.push(existingCategory)
          updateFormDataIncidentCategories()
        }
        incidentCategorySearchTerm.value = ''
      }
    }

    const updateFormDataIncidentCategories = () => {
      formData.value.IncidentCategory = selectedIncidentCategories.value.join(', ')
      validateIncidentCategory() // Trigger validation when incident categories change
    }

    // Initialize categories from existing form data
    const initializeSelectedData = () => {
      // Initialize categories if RiskCategory has existing data
      if (formData.value.RiskCategory) {
        selectedCategories.value = formData.value.RiskCategory.split(', ').filter(cat => cat.trim())
      }
      
      // Initialize business units if AffectedBusinessUnit has existing data
      if (formData.value.AffectedBusinessUnit) {
        selectedBusinessUnits.value = formData.value.AffectedBusinessUnit.split(', ').filter(unit => unit.trim())
      }
      
      // Initialize incident categories if IncidentCategory has existing data
      if (formData.value.IncidentCategory) {
        selectedIncidentCategories.value = formData.value.IncidentCategory.split(', ').filter(cat => cat.trim())
      }
    }

    // Load compliances when component mounts if needed
    onMounted(() => {
      // Fetch categories, business units, and incident categories on component mount
      fetchCategories()
      fetchBusinessUnits()
      fetchIncidentCategories()
      
      // Initialize selected data from existing form data
      initializeSelectedData()
      
      // Add global click listener to close dropdown when clicking outside
      const handleClickOutside = (event) => {
        const complianceSelector = document.querySelector('.compliance-selector')
        const categoryDropdown = document.querySelector('.multi-select-dropdown')
        
        if (complianceSelector && !complianceSelector.contains(event.target)) {
          showDropdown.value = false
        }
        
        // Close category, business unit, and incident category dropdowns when clicking outside
        if (categoryDropdown && !event.target.closest('.multi-select-dropdown')) {
          showCategoryDropdown.value = false
          showBusinessUnitDropdown.value = false
          showIncidentCategoryDropdown.value = false
        }
      }
      
      document.addEventListener('click', handleClickOutside)
      
      // Cleanup listener on unmount
      onUnmounted(() => {
        document.removeEventListener('click', handleClickOutside)
      })
    })

    return {
      formData,
      validationErrors,
      compliances,
      complianceSearchTerm,
      selectedCompliance,
      loadingCompliances,
      showDropdown,
      showComplianceMapping,
      filteredCompliances,
      // Consent management
      consentModalRef,
      showConsentModal,
      // Category dropdown
      availableCategories,
      selectedCategories,
      categorySearchTerm,
      showCategoryDropdown,
      filteredCategories,
      // Business Unit dropdown
      availableBusinessUnits,
      selectedBusinessUnits,
      businessUnitSearchTerm,
      showBusinessUnitDropdown,
      filteredBusinessUnits,
      // Incident Category dropdown
      availableIncidentCategories,
      selectedIncidentCategories,
      incidentCategorySearchTerm,
      showIncidentCategoryDropdown,
      filteredIncidentCategories,
      // Utility methods
      safeSubstring,
      // Methods
      onClassificationChange,
      selectCompliance,
      clearCompliance,
      filterCompliances,
      hideDropdownDelayed,
      // Loading states
      isGeneratingAnalysis,
      // Category methods
      fetchCategories,
      toggleCategoryDropdown,
      filterCategories,
      toggleCategory,
      removeCategory,
      addCustomCategory,
      updateFormDataCategories,
      // Business Unit methods
      fetchBusinessUnits,
      toggleBusinessUnitDropdown,
      filterBusinessUnits,
      toggleBusinessUnit,
      removeBusinessUnit,
      addCustomBusinessUnit,
      updateFormDataBusinessUnits,
      // Incident Category methods
      fetchIncidentCategories,
      toggleIncidentCategoryDropdown,
      filterIncidentCategories,
      toggleIncidentCategory,
      removeIncidentCategory,
      addCustomIncidentCategory,
      updateFormDataIncidentCategories,
      initializeSelectedData,
      // Validation methods
      validateCost,
      validateIncidentTitle,
      validateDescription,
      validateOrigin,
      validateDate,
      validateTime,
      validateRiskPriority,
      validateRiskCategory,
      validateIncidentCategory,
      validateCriticality,
      validatePossibleDamage,
      validateBusinessUnit,
      validateGeographicLocation,
      validateSystemsInvolved,
      validateInitialImpact,
      validateMitigation,
      validateComments,
      validateInternalContacts,
      validateExternalParties,
      validateRegulatoryBodies,
      validateViolatedPolicies,
      validateControlFailures,
      validateAndSubmit,
      submitForm,
      cancel,
      generateAnalysis,
      incidentType,
      isReadyToSubmit
    }
  }
}
</script>

<style>
/* Enhanced validation styles */
.validation-error {
  color: #e74c3c;
  font-size: 0.85rem;
  margin-top: 4px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
  animation: slideIn 0.3s ease-out;
}

.validation-error::before {
  content: "⚠️";
  font-size: 12px;
}

/* Apply red border to fields with validation errors */
input.error, 
textarea.error, 
select.error,
.multi-select-input.error,
.multi-select-dropdown.error .multi-select-input,
input[aria-invalid="true"],
textarea[aria-invalid="true"],
select[aria-invalid="true"] {
  border: 2px solid #e74c3c !important;
  background-color: rgba(231, 76, 60, 0.05) !important;
  box-shadow: 0 0 0 3px rgba(231, 76, 60, 0.1) !important;
}


/* Multi-select dropdown error styling */
.multi-select-dropdown.error {
  border: 2px solid #e74c3c;
  border-radius: 4px;
  background-color: rgba(231, 76, 60, 0.05);
}

.multi-select-dropdown.error .multi-select-input {
  border: none !important;
  background-color: transparent !important;
  box-shadow: none !important;
}

/* Valid state styling */
input:valid:not(:placeholder-shown):not(.error),
textarea:valid:not(:placeholder-shown):not(.error),
select:valid:not(.error) {
  border-color: #27ae60;
  background-color: rgba(39, 174, 96, 0.05);
}

/* Focus states */
input:focus:not(.error),
textarea:focus:not(.error),
select:focus:not(.error) {
  outline: none;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.2);
  border-color: #3498db;
}

/* Error focus states */
input.error:focus,
textarea.error:focus,
select.error:focus,
.multi-select-input.error:focus {
  box-shadow: 0 0 0 3px rgba(231, 76, 60, 0.3) !important;
  border-color: #c0392b !important;
}

/* Required field indicators */
label.required span::after {
  content: " *";
  color: #e74c3c;
  font-weight: bold;
  font-size: 1.1em;
}

/* Real-time validation feedback animation */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Form section error indicators */
.field-third.has-error,
.field-full.has-error {
  border-left: 4px solid #e74c3c;
  padding-left: 12px;
  margin-left: -12px;
  background-color: rgba(231, 76, 60, 0.02);
}

/* Improve visibility of validation messages */
.validation-error {
  background-color: rgba(231, 76, 60, 0.1);
  padding: 6px 10px;
  border-radius: 4px;
  border-left: 4px solid #e74c3c;
  margin-top: 6px;
}

/* Submit button styling when disabled */
.incident-submit-btn:disabled {
  background-color: #bdc3c7 !important;
  cursor: not-allowed !important;
  opacity: 0.6;
}

.incident-submit-btn:disabled:hover {
  background-color: #bdc3c7 !important;
  transform: none !important;
}

</style>
  
  