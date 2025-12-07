<template>
  <div class="event-creation-container">
    <div class="event-creation-title-section">
      <router-link
        to="/event-handling/list"
        class="event-creation-back-btn"
      >
        <svg class="event-creation-back-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
        </svg>
      </router-link>
      <div class="event-creation-title-content">
        <h1 class="event-creation-title">{{ formData.isEdit ? 'Edit Event' : 'Create Event' }}</h1>
        <p class="event-creation-subtitle">{{ formData.isEdit ? 'Edit the event details and supporting evidence' : 'Create a new event with supporting evidence' }}</p>
      </div>
    </div>

    <!-- Progress Steps -->
    <div class="event-creation-steps-wrapper">
      <div v-for="(step, index) in steps" :key="step.number" class="event-creation-step">
        <div :class="`event-creation-step-circle ${
          currentStep >= step.number ? 'event-creation-step-active' : 'event-creation-step-inactive'
        }`">
          <span v-if="currentStep > step.number" class="event-creation-step-check">
            <svg class="event-creation-step-check-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
          </span>
          <span v-else class="event-creation-step-number">{{ step.number }}</span>
        </div>
        <div class="event-creation-step-content">
          <p :class="`event-creation-step-title ${
            currentStep >= step.number ? 'event-creation-step-title-active' : 'event-creation-step-title-inactive'
          }`">
            {{ step.title }}
          </p>
          <p class="event-creation-step-description">{{ step.description }}</p>
        </div>
        <div v-if="index < steps.length - 1" :class="`event-creation-step-connector ${
          currentStep > step.number ? 'event-creation-step-connector-active' : 'event-creation-step-connector-inactive'
        }`" />
      </div>
    </div>

    <!-- Form Content -->
        <!-- Integration Source Banner -->
        <div v-if="formData.source" class="event-creation-integration-banner">
          <div class="event-creation-integration-content">
            <svg class="event-creation-integration-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>
            </svg>
            <div class="event-creation-integration-text">
              <p class="event-creation-integration-title">Creating Event from {{ formData.source }}</p>
              <p class="event-creation-integration-subtitle">This event is being created from an integration source. Some fields have been pre-filled automatically.</p>
            </div>
          </div>
        </div>
        <!-- Step 1: Link to Record -->
        <div v-if="currentStep === 1" class="event-creation-step-content">
          <!-- Template Indicator -->
          <div v-if="formData.title && formData.framework" class="event-creation-template-indicator">
            <div class="event-creation-template-content">
              <svg class="event-creation-template-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
              <div class="event-creation-template-text">
                <p class="event-creation-template-title">Using Template: "{{ formData.title }}"</p>
                <p class="event-creation-template-subtitle">You can modify the framework, module, and record selection below, or proceed to the next step.</p>
              </div>
            </div>
          </div>
          
          <div class="event-creation-form-grid">
            <div class="event-creation-form-group">
              <label class="event-creation-form-label">
                Framework *
                <span class="event-creation-form-hint">(Select compliance framework)</span>
              </label>
              <select
                v-model="formData.framework"
                @change="handleFrameworkChange"
                :disabled="loadingFrameworks"
                class="event-creation-form-select"
                required
              >
                <option value="">
                  {{ loadingFrameworks ? 'Loading frameworks...' : 'Select Framework' }}
                </option>
                <option v-for="framework in frameworks" :key="framework.FrameworkId" :value="framework.FrameworkName">
                  {{ framework.FrameworkName }}
                </option>
              </select>
              <div v-if="frameworksError" class="event-creation-form-error">
                {{ frameworksError }}
                <button @click="fetchFrameworks" class="event-creation-form-retry">
                  Retry
                </button>
              </div>
            </div>

            <div class="event-creation-form-group">
              <label class="event-creation-form-label">
                Module
                <span class="event-creation-form-hint">(Select relevant module)</span>
              </label>
              <select
                v-model="formData.module"
                :disabled="loadingModules"
                class="event-creation-form-select"
              >
                <option value="">
                  {{ loadingModules ? 'Loading modules...' : 'Select Module' }}
                </option>
                <option v-for="module in modules" :key="module.moduleid" :value="module.modulename">{{ module.modulename }}</option>
                <option value="create_new">
                  + Create New Module
                </option>
              </select>
              <div v-if="modulesError" class="event-creation-form-error">
                {{ modulesError }}
                <button @click="fetchModules" class="event-creation-form-retry">
                  Retry
                </button>
              </div>
            </div>

            <div class="event-creation-form-group">
              <label class="event-creation-form-label">
                Specific Record
              </label>
              <select
                v-model="formData.linkedRecord"
                @change="handleRecordChange"
                :disabled="loadingRecords || !formData.frameworkId"
                class="event-creation-form-select"
              >
                <option value="">
                  {{ loadingRecords ? 'Loading records...' : 
                     !formData.frameworkId ? 'Select Framework first' : 
                     'Select Record (Optional)' }}
                </option>
                <option v-for="record in records" :key="record.id" :value="record.name">
                  {{ record.name }} {{ record.identifier ? `(${record.identifier})` : '' }}
                </option>
              </select>
              <div v-if="recordsError" class="event-creation-form-error">
                {{ recordsError }}
                <button @click="() => fetchRecords(formData.frameworkId, formData.module)" class="event-creation-form-retry">
                  Retry
                </button>
              </div>
            </div>
          </div>

          <!-- Event Type Selection -->
          <div class="event-creation-form-group">
            <label class="event-creation-form-label">
              Event Type *
              <span class="event-creation-form-hint">(Event classification)</span>
            </label>
            <select
              v-model="formData.eventTypeId"
              @change="handleEventTypeChange"
              :class="`event-creation-form-select ${
                !formData.eventTypeId ? 'border-red-300 focus:border-red-300' : 'border-gray-300 focus:border-blue-300'
              }`"
              :disabled="!formData.framework || loadingEventTypes"
              required
            >
              <option value="">
                {{ !formData.framework ? 'Select Framework first' : loadingEventTypes ? 'Loading event types...' : 'Select Event Type' }}
              </option>
              <option v-for="eventType in eventTypes" :key="eventType.eventtype_id" :value="eventType.eventtype_id">
                {{ eventType.eventtype }}
              </option>
              <option value="create_new" v-if="formData.framework">
                + Create New Event Type
              </option>
            </select>
            <p v-if="!formData.eventTypeId" class="event-creation-form-error">Event Type is required</p>
            <p v-if="!formData.framework" class="event-creation-form-hint">Please select a framework first to load event types</p>
            <p v-if="eventTypesError" class="event-creation-form-error">{{ eventTypesError }}</p>
          </div>

          <!-- Sub-Event Type Selection -->
          <div v-if="subEventTypes.length > 0" class="event-creation-form-group">
            <label class="event-creation-form-label">
              Sub-Event Type
              <span class="event-creation-form-hint">(Specific sub-category)</span>
            </label>
            <select
              v-model="formData.subEventTypeId"
              :disabled="loadingSubEventTypes"
              class="event-creation-form-select"
            >
              <option value="">
                {{ loadingSubEventTypes ? 'Loading sub-event types...' : 'Select Sub-Event Type (Optional)' }}
              </option>
              <option v-for="subEventType in subEventTypes" :key="subEventType.id" :value="subEventType.id">
                {{ subEventType.name }}
              </option>
            </select>
          </div>

          <button 
            @click="addAnotherRecord"
            class="event-creation-add-record-btn"
          >
            <svg class="event-creation-add-record-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            Add Another Record
            <span v-if="formData.additionalRecords.length > 0" class="event-creation-add-record-badge">
              {{ formData.additionalRecords.length }} added
            </span>
          </button>

          <!-- Display additional records -->
          <div v-if="formData.additionalRecords.length > 0" class="event-creation-additional-records">
            <div class="event-creation-additional-records-header">
              <h4 class="event-creation-additional-records-title">Additional Records</h4>
            </div>
            <div v-for="(record, index) in formData.additionalRecords" :key="index" class="event-creation-additional-record">
              <div class="event-creation-additional-record-header">
                <h5 class="event-creation-additional-record-title">Record {{ index + 2 }}</h5>
                <button
                  @click="removeAdditionalRecord(index)"
                  class="event-creation-additional-record-remove-btn"
                  title="Remove this record"
                >
                  <svg class="event-creation-additional-record-remove-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                  </svg>
                  Remove
                </button>
              </div>
              <div class="event-creation-form-grid">
                <div class="event-creation-form-group">
                  <label class="event-creation-form-label">
                    Framework *
                    <span class="event-creation-form-hint">(Select compliance framework)</span>
                  </label>
                  <select
                    v-model="record.framework"
                    @change="handleAdditionalRecordFrameworkChange(index)"
                    :disabled="loadingFrameworks"
                    class="event-creation-form-select"
                    required
                  >
                    <option value="">
                      {{ loadingFrameworks ? 'Loading frameworks...' : 'Select Framework' }}
                    </option>
                    <option v-for="framework in frameworks" :key="framework.FrameworkId" :value="framework.FrameworkName">
                      {{ framework.FrameworkName }}
                    </option>
                  </select>
                </div>

                <div class="event-creation-form-group">
                  <label class="event-creation-form-label">
                    Module
                    <span class="event-creation-form-hint">(Select relevant module)</span>
                  </label>
                  <select
                    v-model="record.module"
                    @change="handleAdditionalRecordModuleChange(index)"
                    :disabled="loadingModules"
                    class="event-creation-form-select"
                  >
                    <option value="">
                      {{ loadingModules ? 'Loading modules...' : 'Select Module' }}
                    </option>
                    <option v-for="module in modules" :key="module.moduleid" :value="module.modulename">{{ module.modulename }}</option>
                    <option value="create_new">
                      + Create New Module
                    </option>
                  </select>
                </div>

                <div class="event-creation-form-group">
                  <label class="event-creation-form-label">
                    Specific Record
                  </label>
                  <select
                    v-model="record.linkedRecord"
                    @change="handleAdditionalRecordChange(index)"
                    :disabled="loadingRecords || !record.frameworkId"
                    class="event-creation-form-select"
                  >
                    <option value="">
                      {{ loadingRecords ? 'Loading records...' : 
                         !record.frameworkId ? 'Select Framework first' : 
                         'Select Record (Optional)' }}
                    </option>
                    <option v-for="recordOption in record.records" :key="recordOption.id" :value="recordOption.name">
                      {{ recordOption.name }} {{ recordOption.identifier ? `(${recordOption.identifier})` : '' }}
                    </option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 2: Event Details -->
        <div v-if="currentStep === 2" class="event-creation-step-2">
          <div class="event-creation-form-grid">
            <!-- Event Title - Full Width -->
            <div class="event-creation-form-group event-creation-form-group-full">
              <label class="event-creation-form-label">
                Event Title
                <span class="event-creation-form-required">*</span>
                <span class="event-creation-form-hint">(Descriptive title for the event)</span>
              </label>
              <input
                type="text"
                v-model="formData.title"
                placeholder="e.g., Q1 Access Review – Finance Dept"
                :class="`event-creation-form-input ${
                  !formData.title ? 'event-creation-form-input-error' : ''
                }`"
                required
              />
              <p v-if="!formData.title" class="event-creation-form-error">
                <svg class="event-creation-form-error-icon" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                </svg>
                Event title is required
              </p>
            </div>

            <!-- Event ID -->
            <div class="event-creation-form-group">
              <label class="event-creation-form-label">
                Event ID
                <span class="event-creation-form-hint">(Auto-generated)</span>
              </label>
              <input
                type="text"
                :value="generateEventId()"
                disabled
                class="event-creation-form-input event-creation-form-input-disabled"
              />
            </div>

            <!-- Owner -->
            <div class="event-creation-form-group">
              <label class="event-creation-form-label">
                Owner
                <span class="event-creation-form-required">*</span>
                <span class="event-creation-form-hint">(Event owner/creator)</span>
              </label>
              <input
                type="text"
                :value="formData.owner"
                disabled
                class="event-creation-form-input event-creation-form-input-disabled"
                placeholder="Loading current user..."
              />
              <p class="event-creation-form-hint">Automatically set to current user</p>
            </div>

            <!-- Reviewer -->
            <div class="event-creation-form-group">
              <label class="event-creation-form-label">
                Reviewer
                <span class="event-creation-form-required">*</span>
                <span class="event-creation-form-hint">(Approval reviewer)</span>
              </label>
              <select
                v-model="formData.reviewer"
                @change="handleReviewerChange"
                :disabled="loadingReviewers"
                :class="`event-creation-form-select ${
                  !formData.reviewer ? 'event-creation-form-input-error' : ''
                }`"
                required
              >
                <option value="">
                  {{ loadingReviewers ? 'Loading reviewers...' : 'Select Reviewer' }}
                </option>
                <option v-for="reviewer in reviewers" :key="reviewer.id" :value="reviewer.name">
                  {{ reviewer.name }}
                </option>
              </select>
              <p v-if="!formData.reviewer" class="event-creation-form-error">
                <svg class="event-creation-form-error-icon" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                </svg>
                Reviewer is required
              </p>
            </div>

            
            <!-- Description - Full Width -->
            <div class="event-creation-form-group event-creation-form-group-full">
              <label class="event-creation-form-label">
                Description
                <span class="event-creation-form-hint">(Detailed event description)</span>
              </label>
              <textarea
                v-model="formData.description"
                rows="4"
                placeholder="Describe the purpose and scope of this event..."
                class="event-creation-form-textarea"
              />
            </div>
          </div>

          <!-- Event Type Section -->
          <div class="event-creation-section">
            <div class="event-creation-section-header">
              <h3 class="event-creation-section-title">Event Type</h3>
            </div>
            <div class="event-creation-radio-group">
              <label class="event-creation-radio-option">
                <input
                  type="radio"
                  name="recurrence"
                  value="Non-Recurring"
                  v-model="formData.recurrence"
                  class="event-creation-radio-input"
                />
                <span class="event-creation-radio-label">Non-Recurring</span>
              </label>
              <label class="event-creation-radio-option">
                <input
                  type="radio"
                  name="recurrence"
                  value="Recurring"
                  v-model="formData.recurrence"
                  class="event-creation-radio-input"
                />
                <span class="event-creation-radio-label">Recurring</span>
              </label>
            </div>

            <!-- Recurring Options -->
            <div v-if="formData.recurrence === 'Recurring'" class="event-creation-recurring-options">
              <div class="event-creation-form-grid">
                <div class="event-creation-form-group">
                  <label class="event-creation-form-label">Frequency</label>
                  <select
                    v-model="formData.frequency"
                    class="event-creation-form-select"
                  >
                    <option value="">Select Frequency</option>
                    <option v-for="freq in RECURRENCE_FREQUENCIES" :key="freq" :value="freq">{{ freq }}</option>
                  </select>
                </div>
                <div class="event-creation-form-group">
                  <label class="event-creation-form-label">Start Date</label>
                  <input
                    type="date"
                    v-model="formData.startDate"
                    class="event-creation-form-input"
                  />
                </div>
                <div class="event-creation-form-group">
                  <label class="event-creation-form-label">End Date</label>
                  <input
                    type="date"
                    v-model="formData.endDate"
                    class="event-creation-form-input"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- Dynamic Fields Section -->
          <div v-if="Object.keys(dynamicFields).length > 0" class="event-creation-section">
            <div class="event-creation-section-header">
              <h3 class="event-creation-section-title">Additional Fields</h3>
              <p class="event-creation-section-description">Fields specific to your selected framework and event type</p>
            </div>
            
            <div v-if="loadingDynamicFields" class="event-creation-loading">
              <div class="event-creation-loading-spinner"></div>
              <p>Loading additional fields...</p>
            </div>
            
            <div v-else-if="dynamicFieldsError" class="event-creation-error">
              <p>{{ dynamicFieldsError }}</p>
              <button @click="fetchDynamicFields(formData.framework, formData.eventTypeId, formData.subEventTypeId)" class="event-creation-retry-btn">
                Retry
              </button>
            </div>
            
            <div v-else class="event-creation-form-grid">
              <div 
                v-for="(field, fieldKey) in dynamicFields" 
                :key="fieldKey"
                :class="`event-creation-form-group ${
                  field.type === 'textarea' ? 'event-creation-form-group-full' : ''
                }`"
              >
                <label class="event-creation-form-label">
                  {{ field.label }}
                  <span v-if="field.required" class="event-creation-form-required">*</span>
                  <span v-if="field.description" class="event-creation-form-hint">({{ field.description }})</span>
                </label>
                
                <!-- Text Input -->
                <input
                  v-if="field.type === 'text'"
                  type="text"
                  v-model="formData.dynamicFields[fieldKey]"
                  :placeholder="field.placeholder || ''"
                  :class="`event-creation-form-input ${
                    field.required && !formData.dynamicFields[fieldKey] ? 'event-creation-form-input-error' : ''
                  }`"
                  :required="field.required"
                />
                
                <!-- Textarea -->
                <textarea
                  v-else-if="field.type === 'textarea'"
                  v-model="formData.dynamicFields[fieldKey]"
                  :placeholder="field.placeholder || ''"
                  :rows="4"
                  :class="`event-creation-form-textarea ${
                    field.required && !formData.dynamicFields[fieldKey] ? 'event-creation-form-input-error' : ''
                  }`"
                  :required="field.required"
                />
                
                <!-- Select Dropdown -->
                <select
                  v-else-if="field.type === 'select'"
                  v-model="formData.dynamicFields[fieldKey]"
                  :class="`event-creation-form-select ${
                    field.required && !formData.dynamicFields[fieldKey] ? 'event-creation-form-input-error' : ''
                  }`"
                  :required="field.required"
                >
                  <option value="">{{ field.placeholder || 'Select ' + field.label }}</option>
                  <option 
                    v-for="option in field.options" 
                    :key="option.value" 
                    :value="option.value"
                  >
                    {{ option.label }}
                  </option>
                </select>
                
                <!-- Radio Buttons -->
                <div v-else-if="field.type === 'radio'" class="event-creation-radio-group">
                  <label 
                    v-for="option in field.options" 
                    :key="option.value"
                    class="event-creation-radio-option"
                  >
                    <input
                      type="radio"
                      :name="fieldKey"
                      :value="option.value"
                      v-model="formData.dynamicFields[fieldKey]"
                      class="event-creation-radio-input"
                    />
                    <span class="event-creation-radio-label">{{ option.label }}</span>
                  </label>
                </div>
                
                <!-- Section Header -->
                <div v-else-if="field.type === 'section'" class="event-creation-section-header">
                  <h4 class="event-creation-section-title">{{ field.label }}</h4>
                  <p v-if="field.description" class="event-creation-section-description">{{ field.description }}</p>
                  
                  <!-- Render child fields if they exist -->
                  <div v-if="field.children" class="event-creation-form-grid">
                    <div 
                      v-for="(childField, childKey) in field.children" 
                      :key="childKey"
                      :class="`event-creation-form-group ${
                        childField.type === 'textarea' ? 'event-creation-form-group-full' : ''
                      }`"
                    >
                      <label class="event-creation-form-label">
                        {{ childField.label }}
                        <span v-if="childField.required" class="event-creation-form-required">*</span>
                        <span v-if="childField.description" class="event-creation-form-hint">({{ childField.description }})</span>
                      </label>
                      
                      <!-- Child field inputs (same as parent fields) -->
                      <input
                        v-if="childField.type === 'text'"
                        type="text"
                        v-model="formData.dynamicFields[childKey]"
                        :placeholder="childField.placeholder || ''"
                        :class="`event-creation-form-input ${
                          childField.required && !formData.dynamicFields[childKey] ? 'event-creation-form-input-error' : ''
                        }`"
                        :required="childField.required"
                      />
                      
                      <textarea
                        v-else-if="childField.type === 'textarea'"
                        v-model="formData.dynamicFields[childKey]"
                        :placeholder="childField.placeholder || ''"
                        :rows="4"
                        :class="`event-creation-form-textarea ${
                          childField.required && !formData.dynamicFields[childKey] ? 'event-creation-form-input-error' : ''
                        }`"
                        :required="childField.required"
                      />
                      
                      <select
                        v-else-if="childField.type === 'select'"
                        v-model="formData.dynamicFields[childKey]"
                        :class="`event-creation-form-select ${
                          childField.required && !formData.dynamicFields[childKey] ? 'event-creation-form-input-error' : ''
                        }`"
                        :required="childField.required"
                      >
                        <option value="">{{ childField.placeholder || 'Select ' + childField.label }}</option>
                        <option 
                          v-for="option in childField.options" 
                          :key="option.value" 
                          :value="option.value"
                        >
                          {{ option.label }}
                        </option>
                      </select>
                      
                      <!-- Error message for required child fields -->
                      <p v-if="childField.required && !formData.dynamicFields[childKey]" class="event-creation-form-error">
                        <svg class="event-creation-form-error-icon" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                        </svg>
                        {{ childField.label }} is required
                      </p>
                    </div>
                  </div>
                </div>
                
                <!-- Error message for required fields -->
                <p v-if="field.required && !formData.dynamicFields[fieldKey]" class="event-creation-form-error">
                  <svg class="event-creation-form-error-icon" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                  </svg>
                  {{ field.label }} is required
                </p>
              </div>
            </div>
          </div>

          <!-- Template Section -->
          <div class="event-creation-section">
            <div class="event-creation-section-header">
              <h3 class="event-creation-section-title">Template Options</h3>
            </div>
            <div class="event-creation-checkbox-group">
              <label class="event-creation-checkbox-option">
                <input
                  type="checkbox"
                  v-model="formData.isTemplate"
                  class="event-creation-checkbox-input"
                />
                <span class="event-creation-checkbox-label">Save as Template</span>
              </label>
            </div>
            <div v-if="formData.isTemplate" class="event-creation-template-info">
              <div class="event-creation-template-info-content">
                <svg class="event-creation-template-info-icon" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                </svg>
                <div class="event-creation-template-info-text">
                  <strong>Template Mode:</strong> This event will be saved as a template and can be reused for future event creation. Templates will go through the review process before becoming available in the template section.
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 3: Evidence -->
        <div v-if="currentStep === 3" class="space-y-6">
          <!-- Evidence Attachment Section -->
          <div class="evidence-attachment-container">
            <div class="attachment-section">
              <div class="section-header">
                <h2 class="evidence-section-title">Upload Evidence</h2>
              </div>

              <div class="upload-area">
                <!-- Evidence Options - Show by default -->
                <div v-if="!showUploadArea && !showLinkArea" class="evidence-options show">
                  <h3 class="options-title">Choose Evidence Type</h3>
                  <div class="options-container">
                    <div class="option-card" @click="selectUploadOption">
                      <div class="option-icon">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                </svg>
              </div>
                      <h4>Upload an Evidence</h4>
                      <p>Select from local system</p>
            </div>
            
                    <div class="option-card" @click="selectLinkOption">
                      <div class="option-icon">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>
                        </svg>
                      </div>
                      <h4>Link an Evidence</h4>
                      <p>Search</p>
                    </div>
            </div>
            
                  <button class="back-btn" @click="goBackToInitial">
                    <svg class="back-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
                    </svg>
                    Back
                  </button>
            </div>
            
                <!-- Upload Area -->
                <div v-if="showUploadArea" class="file-upload-section show">
                  <div class="upload-header">
                    <h3>Upload Evidence Files</h3>
                    <button class="back-btn small" @click="goBackToOptions">
                      <svg class="back-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
                      </svg>
                      Back to Options
                    </button>
            </div>
            
                  <div class="upload-button-container">
                    <button 
                      class="select-files-btn"
                      @click="triggerFileUpload"
                      :disabled="uploadingFiles"
                    >
                      <svg class="select-files-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path>
                      </svg>
                      {{ uploadingFiles ? 'Uploading...' : 'Select Files' }}
                    </button>
                    
                    <input 
                      ref="fileInput"
                      type="file"
                      multiple
                      accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.txt,.xlsx,.xls"
                      @change="handleFileSelect"
                      style="display: none;"
                    />
              </div>

                  <div class="file-info">
                    <p class="supported-formats">
                      <svg class="info-icon" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                      </svg>
                      Supported formats: PDF, DOC, DOCX, JPG, PNG, TXT, XLSX, XLS
                    </p>
                    <p class="max-size">Maximum file size: 10MB per file</p>
            </div>
            
                  <!-- Selected Files Display -->
                  <div v-if="selectedFiles.length > 0" class="selected-files show">
                    <h3>Selected Files ({{ selectedFiles.length }})</h3>
                    <div class="file-list">
                      <div v-for="(file, index) in selectedFiles" :key="index" class="file-item">
                        <div class="file-info-item">
                          <svg class="file-icon" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"></path>
                          </svg>
                          <div>
                            <div class="file-name">{{ file.name }}</div>
                            <div class="file-size">{{ formatFileSize(file.size) }}</div>
                          </div>
                        </div>
                        <button @click="removeSelectedFile(index)" class="remove-file-btn">
                          <svg class="remove-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                          </svg>
                        </button>
                      </div>
                    </div>
                    
                    <div class="upload-actions">
              <button 
                        @click="uploadSelectedFiles" 
                        class="upload-btn"
                        :disabled="uploadingFiles || selectedFiles.length === 0"
              >
                        <svg v-if="uploadingFiles" class="upload-icon animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                        <svg v-else class="upload-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                        </svg>
                        {{ uploadingFiles ? 'Uploading...' : 'Upload Files' }}
              </button>
              <button 
                        @click="clearSelectedFiles" 
                        class="clear-btn"
                        :disabled="uploadingFiles"
              >
                        <svg class="clear-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                </svg>
                        Clear All
              </button>
            </div>
          </div>
          
                  <!-- Upload Progress -->
                  <div v-if="uploadingFiles" class="upload-progress show">
                    <div class="progress-bar">
                      <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
                    </div>
                    <p>Uploading files... {{ uploadProgress }}%</p>
                  </div>
                  
                  <!-- Success Message -->
                  <div v-if="uploadSuccess" class="success-message show">
                    <svg class="success-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    Files uploaded successfully!
                  </div>
                </div>

                <!-- Link Area -->
                <div v-if="showLinkArea" class="link-evidence-section show">
                  <div class="link-header">
                    <h3>Link Evidence</h3>
                    <button class="back-btn small" @click="goBackToOptions">
                      <svg class="back-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
                      </svg>
                      Back to Options
                    </button>
                  </div>
                  
                  <div class="search-container">
                    <div class="search-input-container">
                      <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                      </svg>
          <input
                        type="text" 
                        placeholder="Search"
                        class="search-input"
                        v-model="searchQuery"
                      />
                    </div>
                    
                    <div class="search-filters">
                      <button 
                        @click="setActiveFilter('All')"
                        :class="['filter-btn', activeFilter === 'All' ? 'active' : '']"
                      >
                        All
                      </button>
                      <button 
                        @click="setActiveFilter('Riskavaire')"
                        :class="['filter-btn', activeFilter === 'Riskavaire' ? 'active' : '']"
                      >
                        Riskavaire
                      </button>
                      <button 
                        @click="setActiveFilter('Integrations')"
                        :class="['filter-btn', activeFilter === 'Integrations' ? 'active' : '']"
                      >
                        Integrations
                      </button>
                      <button 
                        @click="setActiveFilter('Document Handling')"
                        :class="['filter-btn', activeFilter === 'Document Handling' ? 'active' : '']"
                      >
                        Document Handling
                      </button>
                    </div>
                    
                    <div class="search-results">
                      <!-- Loading State -->
                      <div v-if="loadingEvents" class="loading-state">
                        <svg class="loading-icon animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <p>Loading events...</p>
                      </div>
                      
                      <!-- Error State -->
                      <div v-else-if="eventsError" class="error-state">
                        <svg class="error-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.34 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                        </svg>
                        <p>{{ eventsError }}</p>
                        <button @click="fetchAllEvents" class="retry-btn">
                          <svg class="retry-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                          </svg>
                          Retry
                        </button>
                      </div>
                      
                      <!-- No Results -->
                      <div v-else-if="filteredEvents.length === 0" class="no-results-state">
                        <svg class="no-results-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                        </svg>
                        <p v-if="searchQuery.trim()">No events found matching your search.</p>
                        <p v-else-if="activeFilter === 'All'">No events available. Click on a filter to load events.</p>
                        <p v-else-if="activeFilter === 'Document Handling'">No document handling events found.</p>
                        <p v-else>No {{ activeFilter }} events found.</p>
                      </div>
                      
                      <!-- Events List -->
                      <div v-else class="events-list">
                        <div class="events-header">
                          <h4>{{ activeFilter }} Events ({{ filteredEvents.length }})</h4>
                          <button 
                            v-if="selectedEvents.length > 0"
                            @click="linkSelectedEvents"
                            class="link-selected-btn"
                          >
                            <svg class="link-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>
                            </svg>
                            Link {{ selectedEvents.length }} Event(s)
                          </button>
                        </div>
                        
                        <div class="event-items">
                          <div 
                            v-for="event in filteredEvents" 
                            :key="event.id"
                            :class="['event-item', isEventSelected(event) ? 'selected' : '']"
                            @click="selectEvent(event)"
                          >
                            <div class="event-checkbox">
          <input
                                type="checkbox" 
                                :checked="isEventSelected(event)"
                                @click.stop
                                @change="selectEvent(event)"
                              />
                            </div>
                            
                            <div class="event-content">
                              <div class="event-header-info">
                                <h5 class="event-title">{{ event.title }}</h5>
                                <span :class="[
                                  'event-source', 
                                  event.source === 'Jira' ? 'jira-source' : 
                                  event.source === 'Document Handling System' ? 'document-source' : 
                                  'riskavaire-source'
                                ]">
                                  {{ event.source }}
                                </span>
                              </div>
                              
                              <div class="event-details">
                                <div class="event-meta">
                                  <span class="event-framework">{{ event.framework }}</span>
                                  <span class="event-separator">•</span>
                                  <span class="event-timestamp">{{ event.timestamp }}</span>
                                </div>
                                
                                <p v-if="event.description" class="event-description">
                                  {{ event.description.length > 100 ? event.description.substring(0, 100) + '...' : event.description }}
                                </p>
                                
                                <div class="event-status">
                                  <span :class="['status-badge', 'status-' + (event.status || 'new').toLowerCase().replace(' ', '-')]">
                                    {{ event.status || 'New' }}
                                  </span>
                                  <span v-if="event.priority" :class="['priority-badge', 'priority-' + (event.priority || 'medium').toLowerCase()]">
                                    {{ event.priority }}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Error Message -->
              <div v-if="uploadError" class="error-message show">
                <svg class="error-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                {{ uploadError }}
              </div>
            </div>
          </div>

          <div v-if="formData.evidence.length > 0" class="evidence-section">
            <div class="evidence-header">
              <h4 class="evidence-title">
                <svg class="evidence-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                Uploaded Evidence ({{ formData.evidence.length }})
              </h4>
            </div>
            <div class="evidence-list">
              <div v-for="(file, index) in formData.evidence" :key="file.id || index" class="evidence-item" :class="file.status">
                <div class="evidence-item-content">
                  <!-- File Icon with Type Detection -->
                  <div class="evidence-file-icon">
                    <div v-if="file.status === 'uploading'" class="file-icon-uploading">
                      <svg class="animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    </div>
                    <div v-else-if="file.status === 'error'" class="file-icon-error">
                      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                      </svg>
                    </div>
                    <div v-else class="file-icon-success" :class="getFileTypeClass(file.type)">
                      <svg v-if="isPdfFile(file.type)" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
                      </svg>
                      <svg v-else-if="isExcelFile(file.type)" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
                      </svg>
                      <svg v-else-if="isWordFile(file.type)" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
                      </svg>
                      <svg v-else fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                      </svg>
                    </div>
                  </div>
                  
                  <!-- File Info -->
                  <div class="evidence-file-info">
                    <div class="evidence-file-name">{{ file.name }}</div>
                    <div class="evidence-file-details">
                      <span class="evidence-file-size">{{ formatFileSize(file.size) }}</span>
                      <span class="evidence-file-separator">•</span>
                      <span class="evidence-file-type">{{ getFileTypeName(file.type) }}</span>
                      <span v-if="file.status === 'uploading'" class="evidence-status uploading">
                        <svg class="evidence-status-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                        Uploading...
                      </span>
                      <span v-else-if="file.status === 'error'" class="evidence-status error">
                        <svg class="evidence-status-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        Upload failed
                      </span>
                      <span v-else-if="file.status === 'uploaded'" class="evidence-status success">
                        <svg class="evidence-status-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        Ready
                      </span>
                    </div>
                    
                    <!-- Progress Bar -->
                    <div v-if="file.status === 'uploading'" class="evidence-progress">
                      <div class="evidence-progress-bar">
                        <div class="evidence-progress-fill" :style="{ width: file.progress + '%' }"></div>
                      </div>
                      <span class="evidence-progress-text">{{ file.progress }}%</span>
                    </div>
                    
                    <!-- Error Message -->
                    <div v-if="file.status === 'error' && file.error" class="evidence-error-message">
                      {{ file.error }}
                    </div>
                  </div>
                </div>
                
                <!-- Action Buttons -->
                <div class="evidence-actions">
                  <!-- Preview Button -->
                  <button 
                    v-if="file.status === 'uploaded' && isPdfFile(file.type)"
                    @click="previewFile(file)"
                    class="evidence-action-btn evidence-preview-btn"
                    title="Preview file"
                  >
                    <svg class="evidence-action-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                    </svg>
                    <span class="evidence-action-text">Preview</span>
                  </button>
                  
                  <!-- Remove Button -->
                  <button 
                    @click="removeFile(file.id)"
                    class="evidence-action-btn evidence-remove-btn"
                    title="Remove file"
                  >
                    <svg class="evidence-action-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                    <span class="evidence-action-text">Remove</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          

          <!-- Source Information Section -->
          <div v-if="formData.sourceInformation" class="event-creation-source-section">
            <div class="event-creation-source-header">
              <div class="event-creation-source-title-section">
                <div class="event-creation-source-icon">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>
                  </svg>
                </div>
                <div class="event-creation-source-title-content">
                  <h3 class="event-creation-source-title">Source Information</h3>
                  <p class="event-creation-source-subtitle">Event created from integration source</p>
                </div>
              </div>
              <button
                @click="showSourcePopup"
                class="event-creation-source-btn"
              >
                <svg class="event-creation-source-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                </svg>
                View Source Details
              </button>
            </div>
            
            <div class="event-creation-source-content">
              <div class="event-creation-source-grid">
                <div class="event-creation-source-field">
                  <label class="event-creation-source-label">Source System</label>
                  <div class="event-creation-source-value">
                    <svg class="event-creation-source-field-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                    </svg>
                    <span>{{ formData.sourceInformation.source || 'Unknown' }}</span>
                  </div>
                </div>
                
                <div class="event-creation-source-field">
                  <label class="event-creation-source-label">Original Title</label>
                  <div class="event-creation-source-value">
                    <svg class="event-creation-source-field-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                    <span>{{ formData.sourceInformation.title || 'N/A' }}</span>
                  </div>
                </div>
                
                <div class="event-creation-source-field">
                  <label class="event-creation-source-label">Timestamp</label>
                  <div class="event-creation-source-value">
                    <svg class="event-creation-source-field-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <span>{{ formData.sourceInformation.timestamp || 'N/A' }}</span>
                  </div>
                </div>
                
                <div class="event-creation-source-field">
                  <label class="event-creation-source-label">Status</label>
                  <div class="event-creation-source-value">
                    <svg class="event-creation-source-field-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <span :class="getSourceStatusBadgeClass(formData.sourceInformation.status)" class="event-creation-source-status-badge">
                      {{ formData.sourceInformation.status || 'New' }}
                    </span>
                  </div>
                </div>
                
                <div v-if="formData.sourceInformation.suggestedType" class="event-creation-source-field">
                  <label class="event-creation-source-label">Suggested Type</label>
                  <div class="event-creation-source-value">
                    <svg class="event-creation-source-field-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
                    </svg>
                    <span>{{ formData.sourceInformation.suggestedType }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 4: Submit -->
        <div v-if="currentStep === 4" class="event-summary-container">
          <div class="event-summary-header">
            <h3 class="event-summary-title">Event Summary</h3>
            <p class="event-summary-subtitle">Review all details before submitting your event</p>
          </div>
          
          <div class="event-summary-content">
            <div class="event-summary-grid">
              <div class="event-summary-item">
                <label class="event-summary-label">Title</label>
                <div class="event-summary-value">{{ formData.title || 'Not specified' }}</div>
              </div>
              
              <div class="event-summary-item">
                <label class="event-summary-label">Framework</label>
                <div class="event-summary-value">{{ formData.framework || 'Not specified' }}</div>
              </div>
              
              <div class="event-summary-item">
                <label class="event-summary-label">Module</label>
                <div class="event-summary-value">{{ formData.module || 'Not specified' }}</div>
              </div>
              
              <div class="event-summary-item">
                <label class="event-summary-label">Event Type</label>
                <div class="event-summary-value">{{ getEventTypeName() || 'Not specified' }}</div>
              </div>
              
              <div v-if="getSubEventTypeName()" class="event-summary-item">
                <label class="event-summary-label">Sub-Event Type</label>
                <div class="event-summary-value">{{ getSubEventTypeName() }}</div>
              </div>
              
              <div class="event-summary-item">
                <label class="event-summary-label">Owner</label>
                <div class="event-summary-value">{{ formData.owner }}</div>
              </div>
              
              <div class="event-summary-item">
                <label class="event-summary-label">Reviewer</label>
                <div class="event-summary-value">{{ formData.reviewer || 'Not specified' }}</div>
              </div>
              
              <div class="event-summary-item">
                <label class="event-summary-label">Template</label>
                <div class="event-summary-value">
                  <span :class="formData.isTemplate ? 'event-summary-template-yes' : 'event-summary-template-no'">
                    {{ formData.isTemplate ? 'Yes (Will be saved as template)' : 'No (Regular event)' }}
                  </span>
                </div>
              </div>
              
              <div v-if="formData.source" class="event-summary-item">
                <label class="event-summary-label">Source</label>
                <div class="event-summary-value">{{ formData.source }}</div>
              </div>
            </div>
            
            <div v-if="formData.description" class="event-summary-description">
              <label class="event-summary-label">Description</label>
              <div class="event-summary-value">{{ formData.description }}</div>
            </div>
            
            <div v-if="formData.additionalRecords.length > 0" class="event-summary-additional-records">
              <label class="event-summary-label">Additional Records</label>
              <div class="mt-2 space-y-2">
                <div v-for="(record, index) in formData.additionalRecords" :key="index" class="text-sm bg-gray-100 p-2 rounded">
                  <span class="font-medium">{{ record.framework }} - {{ record.module }}</span>
                  <span class="text-gray-600">: {{ record.linkedRecordName }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="flex space-x-4">
            
            <button class="flex-1 inline-flex items-center justify-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors">
              <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
              </svg>
              Submit for Approval
            </button>
          </div>
        </div>

        <!-- Navigation -->
        <div class="event-creation-navigation">
          <button
            @click="handlePrevious"
            :disabled="currentStep === 1"
            class="event-creation-nav-btn event-creation-nav-btn-previous"
          >
            <svg class="event-creation-nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
            </svg>
            Previous
          </button>
          <button
            v-if="currentStep < 4"
            @click="handleNext"
            type="button"
            class="event-creation-nav-btn event-creation-nav-btn-next"
          >
            Next
            <svg class="event-creation-nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
            </svg>
          </button>
          <button
            v-if="currentStep === 4"
            @click="handleSubmit"
            class="event-creation-nav-btn event-creation-nav-btn-submit"
          >
            Submit Event
            <svg class="event-creation-nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
          </button>
        </div>

    <!-- Templates Section -->
      <div class="event-creation-templates">
        <div class="event-creation-templates-header">
          <h3 class="event-creation-templates-title">Event Templates</h3>
          <p class="event-creation-templates-subtitle">
            Use existing events as templates to speed up creation
          </p>
        </div>
        
        <div class="event-creation-templates-table-container">
          <table class="event-creation-templates-table">
            <thead class="event-creation-templates-header-row">
              <tr>
                <th class="event-creation-templates-th">Title</th>
                <th class="event-creation-templates-th">ID</th>
                <th class="event-creation-templates-th">Framework</th>
                <th class="event-creation-templates-th">Module</th>
                <th class="event-creation-templates-th">Event Type</th>
                <th class="event-creation-templates-th">Owner</th>
                <th class="event-creation-templates-th">Reviewer</th>
                <th class="event-creation-templates-th">Date</th>
                <th class="event-creation-templates-th">Action</th>
              </tr>
            </thead>
            <tbody class="event-creation-templates-body">
              <tr v-if="loadingTemplates" class="event-creation-templates-loading">
                <td colspan="9" class="event-creation-templates-loading-cell">
                  Loading templates...
                </td>
              </tr>
              <tr v-else-if="templates.length === 0" class="event-creation-templates-empty">
                <td colspan="9" class="event-creation-templates-empty-cell">
                  No templates available
                </td>
              </tr>
              <tr v-else v-for="template in templates" :key="template.id" class="event-creation-templates-row">
                <td class="event-creation-templates-td">{{ template.title }}</td>
                <td class="event-creation-templates-td event-creation-templates-td-id">{{ template.event_id }}</td>
                <td class="event-creation-templates-td">{{ template.framework }}</td>
                <td class="event-creation-templates-td">{{ template.module }}</td>
                <td class="event-creation-templates-td">{{ template.category }}</td>
                <td class="event-creation-templates-td">{{ template.owner }}</td>
                <td class="event-creation-templates-td">{{ template.reviewer }}</td>
                <td class="event-creation-templates-td">{{ template.date }}</td>
                <td class="event-creation-templates-td">
                  <button 
                    @click="useTemplate(template)" 
                    class="event-creation-templates-use-btn"
                  >
                    <svg class="event-creation-templates-use-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                    </svg>
                    Tailor this Event
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Source Information Popup -->
    <div v-if="showSourceDetailsPopup" class="source-details-overlay">
      <div class="source-details-container">
        <!-- Header -->
        <div class="source-details-header">
          <div class="source-details-header-content">
            <div class="source-details-title-section">
              <h2 class="source-details-title">Source Details</h2>
              <p class="source-details-subtitle">Original information from {{ formData.sourceInformation?.source || 'source system' }}</p>
            </div>
            <button
              @click="closeSourcePopup"
              class="source-details-close-btn"
            >
              <svg class="source-details-close-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>
        
        <!-- Content -->
        <div class="source-details-content">
          <div class="source-details-grid">
            <!-- Left Column -->
            <div class="source-details-section">
              <div class="source-details-details-list">
                <!-- Source System -->
                <div class="source-details-detail-item">
                  <span class="source-details-detail-label">Source System</span>
                  <div class="source-details-detail-value">{{ formData.sourceInformation?.source || 'Unknown' }}</div>
                </div>
                
                <!-- Suggested Type -->
                <div class="source-details-detail-item">
                  <span class="source-details-detail-label">Suggested Type</span>
                  <div class="source-details-detail-value">{{ formData.sourceInformation?.suggestedType || 'Event' }}</div>
                </div>
                
                <!-- Status -->
                <div class="source-details-detail-item">
                  <span class="source-details-detail-label">Status</span>
                  <span :class="getSourceStatusBadgeClass(formData.sourceInformation?.status)" class="source-details-status-badge">
                    {{ formData.sourceInformation?.status || 'New' }}
                  </span>
                </div>
              </div>
            </div>
            
            <!-- Right Column -->
            <div class="source-details-section">
              <div class="source-details-details-list">
                <!-- Raw Title -->
                <div class="source-details-detail-item">
                  <span class="source-details-detail-label">Raw Title</span>
                  <div class="source-details-detail-value">{{ formData.sourceInformation?.title || 'N/A' }}</div>
                </div>
                
                <!-- Timestamp -->
                <div class="source-details-detail-item">
                  <span class="source-details-detail-label">Timestamp</span>
                  <div class="source-details-detail-value">{{ formData.sourceInformation?.timestamp || 'N/A' }}</div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Raw JSON Payload -->
          <div class="source-details-json-section">
            <label class="source-details-json-label">Raw JSON Payload</label>
            <div class="source-details-json-content">
              <pre>{{ JSON.stringify(formData.sourceInformation?.rawData || formData.sourceInformation, null, 2) }}</pre>
            </div>
          </div>
        </div>
        
        <!-- Action Buttons -->
        <div class="source-details-actions">
          <button
            @click="closeSourcePopup"
            class="source-details-btn source-details-btn-close"
          >
            <svg class="source-details-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
            Close
          </button>
        </div>
      </div>
    </div>

    <!-- Create Event Type Modal -->
    <div v-if="showCreateEventTypeModal" class="create-event-type-overlay">
      <div class="create-event-type-container">
        <div class="create-event-type-header">
          <h2 class="create-event-type-title">Create New Event Type</h2>
          <button @click="closeCreateEventTypeModal" class="create-event-type-close-btn">
            <svg class="create-event-type-close-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        
        <div class="create-event-type-content">
          <div class="create-event-type-form-group">
            <label class="create-event-type-label">
              Framework
              <span class="create-event-type-required">*</span>
              <span class="create-event-type-char-count">{{ formData.framework ? formData.framework.length : 0 }}/500</span>
            </label>
            <input
              type="text"
              :value="formData.framework"
              disabled
              class="create-event-type-input create-event-type-input-disabled"
            />
          </div>
          
          <div class="create-event-type-form-group">
            <label class="create-event-type-label">
              Event Type Name
              <span class="create-event-type-required">*</span>
              <span class="create-event-type-char-count">{{ newEventTypeName ? newEventTypeName.length : 0 }}/255</span>
            </label>
            <input
              type="text"
              v-model="newEventTypeName"
              placeholder="Enter new event type name"
              class="create-event-type-input"
              :class="{ 'create-event-type-input-error': newEventTypeError }"
              @input="clearNewEventTypeError"
              maxlength="255"
            />
            <p v-if="newEventTypeError" class="create-event-type-error">{{ newEventTypeError }}</p>
          </div>
        </div>
        
        <div class="create-event-type-footer">
          <button @click="closeCreateEventTypeModal" class="create-event-type-cancel-btn">
            Cancel
          </button>
          <button @click="createNewEventType" class="create-event-type-create-btn" :disabled="creatingEventType">
            <span v-if="creatingEventType">Creating...</span>
            <span v-else>Create Event Type</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Create Module Modal -->
    <div v-if="showCreateModuleModal" class="create-event-type-overlay">
      <div class="create-event-type-container">
        <div class="create-event-type-header">
          <h2 class="create-event-type-title">Create New Module</h2>
          <button @click="closeCreateModuleModal" class="create-event-type-close-btn">
            <svg class="create-event-type-close-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        
        <div class="create-event-type-content">
          <div class="create-event-type-form-group">
            <label class="create-event-type-label">
              Module Name
              <span class="create-event-type-required">*</span>
            </label>
            <input
              type="text"
              v-model="newModuleName"
              placeholder="Enter new module name"
              class="create-event-type-input"
              :class="{ 'create-event-type-input-error': newModuleError }"
              @input="clearNewModuleError"
            />
            <p v-if="newModuleError" class="create-event-type-error">{{ newModuleError }}</p>
          </div>
        </div>
        
        <div class="create-event-type-footer">
          <button @click="closeCreateModuleModal" class="create-event-type-cancel-btn">
            Cancel
          </button>
          <button @click="createNewModule" class="create-event-type-create-btn" :disabled="creatingModule">
            <span v-if="creatingModule">Creating...</span>
            <span v-else>Create Module</span>
          </button>
        </div>
      </div>

    <!-- Popup Modal -->
    <PopupModal />
    
    <!-- Consent Modal is handled globally via App.vue -->
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { RECURRENCE_FREQUENCIES } from '../../utils/constants'
import { eventService, s3Service } from '../../services/api'
import AccessUtils from '../../utils/accessUtils'
import { PopupService } from '../../modules/popus/popupService'
import PopupModal from '../../modules/popus/PopupModal.vue'
import { checkConsentRequired, CONSENT_ACTIONS } from '@/utils/consentManager.js'
import axios from 'axios'

export default {
  name: 'EventCreation',
  components: {
    PopupModal
  },
  setup() {
    const router = useRouter()
    
    const currentStep = ref(1)
    const frameworks = ref([])
    const loadingFrameworks = ref(false)
    const frameworksError = ref(null)
    const modules = ref([])
    const loadingModules = ref(false)
    const modulesError = ref(null)
    const records = ref([])
    const loadingRecords = ref(false)
    const recordsError = ref(null)
    const eventTypes = ref([])
    const loadingEventTypes = ref(false)
    const eventTypesError = ref(null)
    const subEventTypes = ref([])
    const loadingSubEventTypes = ref(false)
    const showCreateEventTypeModal = ref(false)
    const newEventTypeName = ref('')
    const newEventTypeError = ref('')
    const creatingEventType = ref(false)
    const showCreateModuleModal = ref(false)
    const newModuleName = ref('')
    const newModuleError = ref('')
    const creatingModule = ref(false)
    const templates = ref([])
    const loadingTemplates = ref(false)
    const currentUser = ref(null)
    const loadingCurrentUser = ref(false)
    const reviewers = ref([])
    const loadingReviewers = ref(false)
    const showSourceDetailsPopup = ref(false)
    const uploadingFiles = ref(false)
    const uploadProgress = ref({})
    const isDragOver = ref(false)
    
    // Dynamic fields for step 2
    const dynamicFields = ref({})
    const loadingDynamicFields = ref(false)
    const dynamicFieldsError = ref(null)
    
    // Evidence attachment state
    const showEvidenceOptions = ref(true) // Show by default
    const showUploadArea = ref(false)
    const showLinkArea = ref(false)
    const selectedFiles = ref([])
    const uploadSuccess = ref(false)
    const uploadError = ref('')
    const fileInput = ref(null)
    
    // Link evidence state
    const searchQuery = ref('')
    const riskavaireEvents = ref([])
    const integrationEvents = ref([])
    const documentHandlingEvents = ref([])
    const loadingEvents = ref(false)
    const eventsError = ref('')
    const activeFilter = ref('All')
    const selectedEvents = ref([])
    
    // Consent management - using global consentService from App.vue
    
    const formData = ref({
      framework: '',
      frameworkId: '',
      module: '',
      linkedRecord: '',
      linkedRecordId: '',
      linkedRecordName: '',
      additionalRecords: [],
      title: '',
      description: '',
      eventTypeId: '',
      subEventTypeId: '',
      owner: '',
      ownerId: '',
      reviewer: '',
      reviewerId: '',
      recurrence: 'Non-Recurring',
      frequency: '',
      startDate: '',
      endDate: '',
      evidence: [],
      isTemplate: false,
      source: '',
      sourceTimestamp: '',
      sourceInformation: null,
      isEdit: false,
      editEventId: null,
      // Dynamic fields will be added here based on framework/event type selection
      dynamicFields: {}
    })
    
    // Computed property for filtered events
    const filteredEvents = computed(() => {
      let events = []
      
      if (activeFilter.value === 'All') {
        events = [...riskavaireEvents.value, ...integrationEvents.value, ...documentHandlingEvents.value]
      } else if (activeFilter.value === 'Riskavaire') {
        events = riskavaireEvents.value
      } else if (activeFilter.value === 'Integrations') {
        events = integrationEvents.value
      } else if (activeFilter.value === 'Document Handling') {
        events = documentHandlingEvents.value
      }
      
      if (searchQuery.value.trim()) {
        const query = searchQuery.value.toLowerCase()
        events = events.filter(event => 
          (event.title && event.title.toLowerCase().includes(query)) ||
          (event.description && event.description.toLowerCase().includes(query)) ||
          (event.framework && event.framework.toLowerCase().includes(query))
        )
      }
      
      return events
    })

    const steps = [
      { number: 1, title: 'Link to Record', description: 'Associate with existing records and select event type' },
      { number: 2, title: 'Event Details', description: 'Define event information' },
      { number: 3, title: 'Evidence', description: 'Upload supporting documents' },
      { number: 4, title: 'Submit', description: 'Review and submit' }
    ]

    // Check for selected framework from session and pre-select it
    const checkSelectedFrameworkFromSession = async () => {
      try {
        console.log('🔍 DEBUG: Checking for selected framework from session in EventCreation...')
        const response = await axios.get('/api/frameworks/get-selected/', {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        })
        
        console.log('🔍 DEBUG: Framework response in EventCreation:', response.data)
        
        if (response.data && response.data.frameworkId) {
          const frameworkIdFromSession = response.data.frameworkId.toString()
          console.log('✅ DEBUG: Found selected framework in session for EventCreation:', frameworkIdFromSession)
          
          // Pre-select the framework in the form
          const selectedFramework = frameworks.value.find(fw => fw.FrameworkId == frameworkIdFromSession)
          if (selectedFramework) {
            formData.value.frameworkId = selectedFramework.FrameworkId
            formData.value.framework = selectedFramework.FrameworkName
            console.log('✅ DEBUG: Pre-selected framework in EventCreation form:', selectedFramework.FrameworkName)
          }
        } else {
          console.log('ℹ️ DEBUG: No framework filter active - user can select any framework')
        }
      } catch (error) {
        console.error('❌ DEBUG: Error checking selected framework in EventCreation:', error)
      }
    }

    // Fetch frameworks from API
    const fetchFrameworks = async () => {
      loadingFrameworks.value = true
      frameworksError.value = null
      
      try {
        const response = await eventService.getFrameworks()
        if (response.data.success) {
          frameworks.value = response.data.frameworks
          
          // After frameworks are loaded, check for selected framework from session
          await checkSelectedFrameworkFromSession()
        } else {
          frameworksError.value = 'Failed to fetch frameworks'
        }
      } catch (error) {
        console.error('Error fetching frameworks:', error)
        PopupService.error('Error loading frameworks. Please try again.', 'Error')
        // Fallback to hardcoded frameworks if API fails
        frameworks.value = [
          { FrameworkId: 1, FrameworkName: 'NIST' },
          { FrameworkId: 2, FrameworkName: 'ISO 27001' },
          { FrameworkId: 3, FrameworkName: 'COBIT' },
          { FrameworkId: 4, FrameworkName: 'PCI DSS' },
          { FrameworkId: 5, FrameworkName: 'HIPAA' },
          { FrameworkId: 6, FrameworkName: 'SOX' },
          { FrameworkId: 7, FrameworkName: 'GDPR' }
        ]
      } finally {
        loadingFrameworks.value = false
      }
    }

    const fetchModules = async () => {
      loadingModules.value = true
      modulesError.value = null
      
      try {
        const response = await eventService.getModules()
        if (response.data.success) {
          modules.value = response.data.modules
        } else {
          modulesError.value = 'Failed to fetch modules'
        }
      } catch (error) {
        console.error('Error fetching modules:', error)
        PopupService.error('Error loading modules. Please try again.', 'Error')
        // Fallback to hardcoded modules if API fails
        modules.value = [
          { moduleid: 1, modulename: 'Policy Management' },
          { moduleid: 2, modulename: 'Compliance Management' },
          { moduleid: 3, modulename: 'Audit Management' },
          { moduleid: 4, modulename: 'Incident Management' },
          { moduleid: 5, modulename: 'Risk Management' }
        ]
      } finally {
        loadingModules.value = false
      }
    }

    const fetchEventTypes = async (frameworkName) => {
      if (!frameworkName) {
        eventTypes.value = []
        eventTypesError.value = null
        return
      }
      
      loadingEventTypes.value = true
      eventTypesError.value = null
      
      try {
        // Trim the framework name to remove any extra whitespace
        const trimmedFrameworkName = frameworkName.trim()
        console.log('Fetching event types for framework:', `"${trimmedFrameworkName}"`)
        const response = await eventService.getEventTypesByFramework(trimmedFrameworkName)
        
        console.log('Event types response:', response.data)
        
        if (response.data.success) {
          eventTypes.value = response.data.event_types || []
          
          // Check if no event types were found
          if (eventTypes.value.length === 0) {
            const debugInfo = response.data.debug_info
            if (debugInfo && debugInfo.available_frameworks) {
              console.warn('No event types found. Available frameworks in database:', debugInfo.available_frameworks)
              eventTypesError.value = `No event types found for "${frameworkName}". Available frameworks: ${debugInfo.available_frameworks.join(', ')}`
            } else {
              eventTypesError.value = `No event types found for "${frameworkName}"`
            }
          } else {
            console.log(`Successfully loaded ${eventTypes.value.length} event types`)
          }
        } else {
          eventTypesError.value = response.data.message || 'Failed to fetch event types'
          eventTypes.value = []
        }
      } catch (error) {
        console.error('Error fetching event types:', error)
        if (error.response && error.response.data && error.response.data.message) {
          eventTypesError.value = error.response.data.message
        } else {
          eventTypesError.value = 'Error loading event types: ' + (error.message || 'Unknown error')
        }
        eventTypes.value = []
      } finally {
        loadingEventTypes.value = false
      }
    }

    // Fetch records based on framework and module
    const fetchRecords = async (frameworkId, module) => {
      if (!frameworkId) {
        records.value = []
        return
      }
      
      // If no module is selected, we can still fetch records but with empty module
      // The backend should handle this case

      loadingRecords.value = true
      recordsError.value = null
      
      try {
        const response = await eventService.getRecordsByModule(frameworkId, module)
        if (response.data.success) {
          records.value = response.data.records
        } else {
          recordsError.value = 'Failed to fetch records'
        }
      } catch (error) {
        console.error('Error fetching records:', error)
        recordsError.value = 'Error loading records. Please try again.'
        records.value = []
      } finally {
        loadingRecords.value = false
      }
    }

    // Fetch event templates
    const fetchTemplates = async () => {
      loadingTemplates.value = true
      
      try {
        const response = await eventService.getTemplates()
        if (response.data.success) {
          templates.value = response.data.templates
        }
      } catch (error) {
        console.error('Error fetching templates:', error)
        // Fallback to hardcoded templates
        templates.value = [
          {
            id: 1,
            title: 'Q4 Access Review - IT',
            event_id: 'EVT-2025-1188',
            framework: 'ISO 27001',
            module: 'Compliance → A.9.2.3',
            category: 'Access Review',
            owner: 'Sarah Lee',
            reviewer: 'CISO',
            date: '15/12'
          },
          {
            id: 2,
            title: 'Annual DR Drill',
            event_id: 'EVT-2025-1123',
            framework: 'SOC 2',
            module: 'BCP → DR Plan',
            category: 'DR Drill',
            owner: 'Rahul Khanna',
            reviewer: 'COO',
            date: '20/11'
          }
        ]
      } finally {
        loadingTemplates.value = false
      }
    }

    // Fetch current user information
    const fetchCurrentUser = async () => {
      loadingCurrentUser.value = true
      
      try {
        const userId = localStorage.getItem('user_id')
        if (!userId) {
          console.error('No user ID found in localStorage')
          return
        }
        
        const response = await eventService.getCurrentUser(userId)
        if (response.data.success) {
          currentUser.value = response.data.user
          formData.value.owner = response.data.user.name
          formData.value.ownerId = response.data.user.id
        }
      } catch (error) {
        console.error('Error fetching current user:', error)
        // Fallback to default values
        formData.value.owner = 'Current User'
        formData.value.ownerId = 1
      } finally {
        loadingCurrentUser.value = false
      }
    }

    // Fetch users for reviewer selection
    const fetchReviewers = async () => {
      loadingReviewers.value = true
      
      try {
        const userId = localStorage.getItem('user_id')
        if (!userId) {
          console.error('No user ID found in localStorage')
          return
        }
        
        const response = await eventService.getUsersForReviewer(userId)
        if (response.data.success) {
          reviewers.value = response.data.users
        }
      } catch (error) {
        console.error('Error fetching reviewers:', error)
        // Fallback to hardcoded reviewers
        reviewers.value = [
          { id: 1, name: 'Priya Sinha' },
          { id: 2, name: 'CISO' },
          { id: 3, name: 'IT Head' }
        ]
      } finally {
        loadingReviewers.value = false
      }
    }

    // Fetch dynamic fields based on framework and event type selection
    const fetchDynamicFields = async (frameworkName, eventTypeId, subEventTypeId = null) => {
      if (!frameworkName || !eventTypeId) {
        dynamicFields.value = {}
        return
      }
      
      loadingDynamicFields.value = true
      dynamicFieldsError.value = null
      
      try {
        console.log('Fetching dynamic fields for:', { frameworkName, eventTypeId, subEventTypeId })
        const response = await eventService.getDynamicFieldsForEvent(frameworkName, eventTypeId, subEventTypeId)
        if (response.data.success) {
          dynamicFields.value = response.data.fields
          console.log('Dynamic fields loaded:', dynamicFields.value)
        } else {
          dynamicFieldsError.value = 'Failed to fetch dynamic fields'
        }
      } catch (error) {
        console.error('Error fetching dynamic fields:', error)
        dynamicFieldsError.value = 'Error loading dynamic fields'
        dynamicFields.value = {}
      } finally {
        loadingDynamicFields.value = false
      }
    }

    const handleNext = async () => {
      // Validate current step before proceeding
      if (currentStep.value === 1) {
        // Validate primary record - only framework is required now
        if (!formData.value.framework) {
          PopupService.warning('Please select a Framework.', 'Validation Error')
          return
        }
        
        // Validate event type
        if (!formData.value.eventTypeId) {
          PopupService.warning('Please select an Event Type.', 'Validation Error')
          return
        }
        
        // Validate additional records if any - only framework is required now
        for (let i = 0; i < formData.value.additionalRecords.length; i++) {
          const record = formData.value.additionalRecords[i]
          if (!record.framework) {
            PopupService.warning(`Please select a Framework for additional record ${i + 1}.`, 'Validation Error')
            return
          }
        }
        
        // Fetch dynamic fields when moving to step 2
        await fetchDynamicFields(
          formData.value.framework, 
          formData.value.eventTypeId, 
          formData.value.subEventTypeId
        )
      } else if (currentStep.value === 2) {
        // Validate event details
        if (!formData.value.title || !formData.value.reviewer) {
          PopupService.warning('Please fill in all required fields: Title and Reviewer.', 'Validation Error')
          return
        }
        
        // Validate dynamic fields
        for (const [fieldKey, field] of Object.entries(dynamicFields.value)) {
          if (field.required && !formData.value.dynamicFields[fieldKey]) {
            PopupService.warning(`Please fill in the required field: ${field.label}.`, 'Validation Error')
            return
          }
          
          // Validate nested fields if they exist
          if (field.type === 'section' && field.children) {
            for (const [childKey, childField] of Object.entries(field.children)) {
              if (childField.required && !formData.value.dynamicFields[childKey]) {
                PopupService.warning(`Please fill in the required field: ${childField.label}.`, 'Validation Error')
                return
              }
            }
          }
        }
      }
      
      if (currentStep.value < 4) currentStep.value++
    }

    const handlePrevious = () => {
      if (currentStep.value > 1) currentStep.value--
    }

    const handleSubmit = async () => {
      try {
        // Validate all required fields before submitting
        if (!formData.value.title) {
          PopupService.warning('Event title is required. Please go back to step 2 and fill in the title.', 'Validation Error')
          return
        }
        
        if (!formData.value.framework) {
          PopupService.warning('Framework is required. Please go back to step 1 and select a framework.', 'Validation Error')
          return
        }
        
        if (!formData.value.eventTypeId) {
          PopupService.warning('Event Type is required. Please go back to step 1 and select an event type.', 'Validation Error')
          return
        }
        
        if (!formData.value.reviewer) {
          PopupService.warning('Reviewer is required. Please go back to step 2 and select a reviewer.', 'Validation Error')
          return
        }
        
        // Validate additional records if any - only framework is required now
        for (let i = 0; i < formData.value.additionalRecords.length; i++) {
          const record = formData.value.additionalRecords[i]
          if (!record.framework) {
            PopupService.warning(`Additional record ${i + 1} is incomplete. Please go back to step 1 and select a framework.`, 'Validation Error')
            return
          }
        }
        
        const userId = localStorage.getItem('user_id')
        
        // Prepare evidence data for backend
        console.log('DEBUG: All evidence files:', formData.value.evidence)
        console.log('DEBUG: Evidence files with uploaded status:', formData.value.evidence.filter(file => file.status === 'uploaded'))
        
        const evidenceData = formData.value.evidence
          .filter(file => file.status === 'uploaded' && file.s3Url)
          .map(file => ({
            file_name: file.name,
            s3_url: file.s3Url,
            s3_key: file.s3Key,
            file_size: file.size,
            file_type: file.type,
            uploaded_at: new Date().toISOString()
          }))
        
        console.log('DEBUG: Prepared evidence data:', evidenceData)
        
        // Convert evidence data to JSON string for backend
        const evidenceJsonString = JSON.stringify(evidenceData)
        console.log('DEBUG: Evidence JSON string:', evidenceJsonString)

        const eventData = {
          title: formData.value.title,
          description: formData.value.description,
          framework_id: formData.value.frameworkId,
          framework_name: formData.value.framework,
          module: formData.value.module,
          linked_record_type: formData.value.module?.toLowerCase(),
          linked_record_id: formData.value.linkedRecordId,
          linked_record_name: formData.value.linkedRecordName,
          event_type_id: formData.value.eventTypeId,
          sub_event_type_id: formData.value.subEventTypeId,
          category: getEventTypeName(), // Send the event type name as category
          recurrence_type: formData.value.recurrence,
          frequency: formData.value.frequency,
          start_date: formData.value.startDate,
          end_date: formData.value.endDate,
          // Remove hardcoded status - let backend determine based on reviewer assignment
          priority: 'Medium',
          owner_id: formData.value.ownerId,
          reviewer_id: formData.value.reviewerId,
          created_by_id: formData.value.ownerId,
          user_id: userId,  // Add user_id for backend authentication
          is_template: formData.value.isTemplate,  // Add template selection
          evidence: evidenceJsonString,  // Include evidence files as JSON string
          dynamic_fields: formData.value.dynamicFields,  // Include dynamic fields
          additional_records: formData.value.additionalRecords.map(record => ({
            framework_id: record.frameworkId,
            framework_name: record.framework,
            module: record.module,
            linked_record_type: record.module?.toLowerCase(),
            linked_record_id: record.linkedRecordId,
            linked_record_name: record.linkedRecordName
          }))
        }

        console.log('DEBUG: Final eventData being sent:', eventData)
        console.log('DEBUG: Evidence in eventData:', eventData.evidence)
        
        let response
        if (formData.value.isEdit && formData.value.editEventId) {
          // Update existing event (no consent required for updates)
          console.log('DEBUG: Updating existing event with ID:', formData.value.editEventId)
          response = await eventService.updateEvent(formData.value.editEventId, eventData)
          if (response.data.success) {
            PopupService.success('Event updated successfully!', 'Success')
          }
        } else {
          // Create new event - check consent first
          console.log('🔍 [Consent] Checking consent requirement for create_event')
          
          // Use the global consent service instead of local ref
          const consentService = (await import('@/services/consentService.js')).default;
          
          const canProceed = await consentService.checkAndRequestConsent(
            CONSENT_ACTIONS.CREATE_EVENT
          );
          
          // If user declined consent, stop here
          if (!canProceed) {
            console.log('❌ [Consent] User declined consent')
            PopupService.warning('Event creation cancelled - consent is required')
            return;
          }
          
          // Get consent config to include in request
          const consentCheck = await checkConsentRequired(CONSENT_ACTIONS.CREATE_EVENT)
          if (consentCheck.required && consentCheck.config) {
            console.log('✅ [Consent] User accepted consent, including consent data in request')
            // Add consent data to eventData
            eventData.consent_accepted = true
            eventData.consent_config_id = consentCheck.config.config_id
            eventData.framework_id = eventData.framework_id || localStorage.getItem('framework_id')
          }
          
          // Create new event
          response = await eventService.createEvent(eventData)
          if (response.data.success) {
            const totalEvents = response.data.total_events_created || 1
            const templateMessage = formData.value.isTemplate ? ' as templates' : ''
            
            if (totalEvents === 1) {
              const status = response.data.events?.[0]?.Status || 'created'
              PopupService.success(`Event created successfully${templateMessage} with status: ${status}!`, 'Success')
            } else {
              PopupService.success(`${totalEvents} events created successfully${templateMessage}! (1 primary + ${totalEvents-1} additional records)`, 'Success')
            }
          }
        }
        
        if (response.data.success) {
          // Navigate to events list page
          router.push('/event-handling/list')
          
          // Check if this was created from integration data and update status
          const integrationData = sessionStorage.getItem('integrationEventData')
          if (integrationData) {
            try {
              const data = JSON.parse(integrationData)
              if (data.integrationItemId) {
                // Store success status for the queue to pick up
                sessionStorage.setItem('eventCreationStatus', JSON.stringify({
                  success: true,
                  integrationItemId: data.integrationItemId,
                  eventId: response.data.event?.id
                }))
              }
            } catch (error) {
              console.error('Error processing integration data:', error)
            }
          }
          
          // Reset form or redirect
          console.log('Event created:', response.data)
        } else {
          // Check if it's a database schema error
          if (response.data.message && response.data.message.includes('schema mismatch')) {
            console.log('Database schema mismatch detected, creating events table...')
            try {
              const tableResponse = await eventService.createEventsTable()
              if (tableResponse.data.success) {
                PopupService.success('Events table created successfully. Please try creating the event again.', 'Success')
                // Retry creating the event
                const retryResponse = await eventService.createEvent(eventData)
                if (retryResponse.data.success) {
                  const totalEvents = retryResponse.data.total_events_created || 1
                  if (totalEvents === 1) {
                    PopupService.success('Event created successfully!', 'Success')
                  } else {
                    PopupService.success(`${totalEvents} events created successfully! (1 primary + ${totalEvents-1} additional records)`, 'Success')
                  }
                  
                  // Navigate to events list page
                  router.push('/event-handling/list')
                  
                  // Check if this was created from integration data and update status
                  const integrationData = sessionStorage.getItem('integrationEventData')
                  if (integrationData) {
                    try {
                      const data = JSON.parse(integrationData)
                      if (data.integrationItemId) {
                        // Store success status for the queue to pick up
                        sessionStorage.setItem('eventCreationStatus', JSON.stringify({
                          success: true,
                          integrationItemId: data.integrationItemId,
                          eventId: retryResponse.data.event?.id
                        }))
                      }
                    } catch (error) {
                      console.error('Error processing integration data:', error)
                    }
                  }
                  
                  console.log('Event created after table creation:', retryResponse.data)
                } else {
                  PopupService.error('Failed to create event after table creation: ' + retryResponse.data.message, 'Error')
                }
              } else {
                PopupService.error('Failed to create events table: ' + tableResponse.data.message, 'Error')
              }
            } catch (tableError) {
              console.error('Error creating events table:', tableError)
              PopupService.error('Failed to create events table. Please contact administrator.', 'Error')
            }
          } else {
            PopupService.error('Failed to create event: ' + response.data.message, 'Error')
          }
        }
      } catch (error) {
        console.error('Error creating event:', error)
        PopupService.error('Error creating event. Please try again.', 'Error')
      }
    }

    const generateEventId = () => {
      return `EVT-${new Date().getFullYear()}-${Math.floor(Math.random() * 9999).toString().padStart(4, '0')}`
    }

    const getEventTypeName = () => {
      if (!formData.value.eventTypeId) return ''
      const eventType = eventTypes.value.find(et => et.eventtype_id === formData.value.eventTypeId)
      return eventType ? eventType.eventtype : ''
    }

    const getSubEventTypeName = () => {
      if (!formData.value.subEventTypeId) return ''
      const subEventType = subEventTypes.value.find(set => set.id === formData.value.subEventTypeId)
      return subEventType ? subEventType.name : ''
    }

    // Create Event Type Modal Methods
    const openCreateEventTypeModal = () => {
      showCreateEventTypeModal.value = true
      newEventTypeName.value = ''
      newEventTypeError.value = ''
    }

    const closeCreateEventTypeModal = () => {
      showCreateEventTypeModal.value = false
      newEventTypeName.value = ''
      newEventTypeError.value = ''
      formData.value.eventTypeId = '' // Reset selection
    }

    const clearNewEventTypeError = () => {
      newEventTypeError.value = ''
    }

    const createNewEventType = async () => {
      if (!newEventTypeName.value.trim()) {
        newEventTypeError.value = 'Event type name is required'
        return
      }

      // Validate framework name length (max 500 characters)
      if (formData.value.framework && formData.value.framework.length > 500) {
        newEventTypeError.value = 'Framework name is too long (maximum 500 characters)'
        return
      }

      // Validate event type name length (max 255 characters)
      if (newEventTypeName.value.trim().length > 255) {
        newEventTypeError.value = 'Event type name is too long (maximum 255 characters)'
        return
      }

      creatingEventType.value = true
      newEventTypeError.value = ''

      try {
        const response = await eventService.createEventType(formData.value.framework, newEventTypeName.value.trim())
        
        if (response.data.success) {
          // Add the new event type to the list
          eventTypes.value.push(response.data.event_type)
          
          // Select the newly created event type
          formData.value.eventTypeId = response.data.event_type.eventtype_id
          
          // Close the modal
          closeCreateEventTypeModal()
          
          PopupService.success('Event type created successfully!', 'Success')
        } else {
          newEventTypeError.value = response.data.message || 'Failed to create event type'
        }
      } catch (error) {
        console.error('Error creating event type:', error)
        const errorMessage = error.response?.data?.message || 'Failed to create event type'
        newEventTypeError.value = errorMessage
      } finally {
        creatingEventType.value = false
      }
    }

    // Create Module Modal Methods
    const openCreateModuleModal = () => {
      showCreateModuleModal.value = true
      newModuleName.value = ''
      newModuleError.value = ''
    }

    const closeCreateModuleModal = () => {
      showCreateModuleModal.value = false
      newModuleName.value = ''
      newModuleError.value = ''
      formData.value.module = '' // Reset selection
    }

    const clearNewModuleError = () => {
      newModuleError.value = ''
    }

    const createNewModule = async () => {
      if (!newModuleName.value.trim()) {
        newModuleError.value = 'Module name is required'
        return
      }

      creatingModule.value = true
      newModuleError.value = ''

      try {
        const response = await eventService.createModule(newModuleName.value.trim())
        
        if (response.data.success) {
          // Add the new module to the list
          modules.value.push(response.data.module)
          
          // Select the newly created module
          formData.value.module = response.data.module.modulename
          
          // Close the modal
          closeCreateModuleModal()
          
          PopupService.success('Module created successfully!', 'Success')
        } else {
          newModuleError.value = response.data.message || 'Failed to create module'
        }
      } catch (error) {
        console.error('Error creating module:', error)
        const errorMessage = error.response?.data?.message || 'Failed to create module'
        newModuleError.value = errorMessage
      } finally {
        creatingModule.value = false
      }
    }

    // Handle framework selection change
    const handleFrameworkChange = () => {
      const selectedFramework = frameworks.value.find(fw => fw.FrameworkName === formData.value.framework)
      if (selectedFramework) {
        formData.value.frameworkId = selectedFramework.FrameworkId
        // Clear records, event type, and sub-event type when framework changes
        formData.value.linkedRecord = ''
        formData.value.linkedRecordId = ''
        formData.value.linkedRecordName = ''
        formData.value.eventTypeId = ''
        formData.value.subEventTypeId = ''
        records.value = []
        subEventTypes.value = []
        // Fetch event types for the selected framework
        fetchEventTypes(formData.value.framework)
      }
    }

    // Handle record selection change
    const handleRecordChange = () => {
      const selectedRecord = records.value.find(record => record.name === formData.value.linkedRecord)
      if (selectedRecord) {
        formData.value.linkedRecordId = selectedRecord.id
        formData.value.linkedRecordName = selectedRecord.name
      }
    }

    // Handle reviewer selection change
    const handleReviewerChange = () => {
      const selectedReviewer = reviewers.value.find(reviewer => reviewer.name === formData.value.reviewer)
      if (selectedReviewer) {
        formData.value.reviewerId = selectedReviewer.id
      }
    }

    // Use template to populate form
    const useTemplate = (template) => {
      formData.value.title = template.title
      formData.value.framework = template.framework
      formData.value.module = template.module
      // Note: Template category will be used to find matching event type
      // formData.value.eventTypeId will be set after fetching event types
      formData.value.owner = template.owner
      formData.value.reviewer = template.reviewer
      
      // Find framework ID
      const selectedFramework = frameworks.value.find(fw => fw.FrameworkName === template.framework)
      if (selectedFramework) {
        formData.value.frameworkId = selectedFramework.FrameworkId
        // Fetch records for the selected framework and module
        fetchRecords(selectedFramework.FrameworkId, template.module)
        // Fetch event types for the framework and find matching event type
        fetchEventTypes(template.framework).then(() => {
          // Find matching event type based on template category
          if (template.category) {
            const matchingEventType = eventTypes.value.find(et => et.eventtype === template.category)
            if (matchingEventType) {
              formData.value.eventTypeId = matchingEventType.eventtype_id
            }
          }
        })
      }
      
      // Start from step 1 so user can modify framework/module if needed
      currentStep.value = 1
      
      // Scroll to the form section to make it visible
      setTimeout(() => {
        const formElement = document.querySelector('.event-creation-form')
        if (formElement) {
          formElement.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
          })
        }
      }, 100)
      
      // Show success message
      PopupService.success(`Template "${template.title}" has been loaded into the form. You can now modify the details and proceed with creating your event.`, 'Template Loaded')
    }

    // Add another record functionality
    const addAnotherRecord = () => {
      formData.value.additionalRecords.push({
        framework: '',
        frameworkId: '',
        module: '',
        linkedRecord: '',
        linkedRecordId: '',
        linkedRecordName: '',
        records: []
      })
    }

    // Remove additional record
    const removeAdditionalRecord = (index) => {
      formData.value.additionalRecords.splice(index, 1)
    }

    // Handle additional record framework change
    const handleAdditionalRecordFrameworkChange = (index) => {
      const record = formData.value.additionalRecords[index]
      const selectedFramework = frameworks.value.find(fw => fw.FrameworkName === record.framework)
      if (selectedFramework) {
        record.frameworkId = selectedFramework.FrameworkId
        // Clear records when framework changes
        record.linkedRecord = ''
        record.linkedRecordId = ''
        record.linkedRecordName = ''
        record.records = []
      }
    }

    // Handle additional record module change
    const handleAdditionalRecordModuleChange = (index) => {
      const record = formData.value.additionalRecords[index]
      if (record.frameworkId) {
        fetchAdditionalRecords(record.frameworkId, record.module || '', index)
      }
    }

    // Handle additional record selection change
    const handleAdditionalRecordChange = (index) => {
      const record = formData.value.additionalRecords[index]
      const selectedRecord = record.records.find(rec => rec.name === record.linkedRecord)
      if (selectedRecord) {
        record.linkedRecordId = selectedRecord.id
        record.linkedRecordName = selectedRecord.name
      }
    }

    // Fetch records for additional record
    const fetchAdditionalRecords = async (frameworkId, module, index) => {
      if (!frameworkId) {
        formData.value.additionalRecords[index].records = []
        return
      }

      try {
        const response = await eventService.getRecordsByModule(frameworkId, module)
        if (response.data.success) {
          formData.value.additionalRecords[index].records = response.data.records
        } else {
          console.error('Failed to fetch records for additional record')
          formData.value.additionalRecords[index].records = []
        }
      } catch (error) {
        console.error('Error fetching records for additional record:', error)
        formData.value.additionalRecords[index].records = []
      }
    }

    // Source popup functions
    const showSourcePopup = () => {
      showSourceDetailsPopup.value = true
    }

    const closeSourcePopup = () => {
      showSourceDetailsPopup.value = false
    }

    const getSourceStatusBadgeClass = (status) => {
      const statusClasses = {
        'New': 'bg-blue-100 text-blue-800',
        'In Progress': 'bg-yellow-100 text-yellow-800',
        'Completed': 'bg-green-100 text-green-800',
        'Approved': 'bg-green-100 text-green-800',
        'Rejected': 'bg-red-100 text-red-800',
        'Processing': 'bg-purple-100 text-purple-800',
        'Archived': 'bg-gray-100 text-gray-800',
        'Draft': 'bg-gray-100 text-gray-800',
        'To Do': 'bg-blue-100 text-blue-800',
        'Done': 'bg-green-100 text-green-800'
      }
      return statusClasses[status] || 'bg-gray-100 text-gray-800'
    }

    // File upload methods
    const handleFileSelect = (event) => {
      const files = Array.from(event.target.files)
      if (files.length > 0) {
        // Validate files
        const validFiles = []
        for (const file of files) {
          // Validate file size (10MB limit)
          if (file.size > 10 * 1024 * 1024) {
            PopupService.warning(`File "${file.name}" is too large. Maximum size is 10MB.`, 'File Size Error')
            continue
          }

          // Validate file type
          const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'image/jpeg', 'image/jpg', 'image/png', 'text/plain', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel']
          if (!allowedTypes.includes(file.type)) {
            PopupService.warning(`File "${file.name}" has an unsupported format. Supported formats: PDF, DOC, DOCX, JPG, PNG, TXT, XLSX, XLS`, 'File Type Error')
            continue
          }

          validFiles.push(file)
        }
        
        if (validFiles.length > 0) {
          selectedFiles.value.push(...validFiles)
          uploadError.value = ''
        }
      }
    }

    const handleDrop = (event) => {
      event.preventDefault()
      isDragOver.value = false
      const files = Array.from(event.dataTransfer.files)
      if (files.length > 0) {
        uploadFiles(files)
      }
    }

    const handleDragOver = (event) => {
      event.preventDefault()
      isDragOver.value = true
    }

    const handleDragLeave = (event) => {
      event.preventDefault()
      isDragOver.value = false
    }

    // Legacy methods - kept for backward compatibility
    const openFileDialog = () => {
      if (!uploadingFiles.value) {
        const fileInput = document.querySelector('input[type="file"]:not([webkitdirectory])')
        if (fileInput) {
          fileInput.click()
        }
      }
    }

    const openFolderDialog = () => {
      if (!uploadingFiles.value) {
        const folderInput = document.querySelector('input[webkitdirectory]')
        if (folderInput) {
          folderInput.click()
        }
      }
    }

    const handleFolderSelect = (event) => {
      const files = Array.from(event.target.files)
      if (files.length > 0) {
        // Filter files by supported types
        const supportedFiles = files.filter(file => {
          const allowedTypes = ['application/pdf', 'text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
          return allowedTypes.includes(file.type)
        })
        
        if (supportedFiles.length > 0) {
          uploadFiles(supportedFiles)
        } else {
          PopupService.warning('No supported files found in the selected folder. Supported formats: PDF, CSV, XLSX, DOC, TXT', 'No Supported Files')
        }
      }
    }

    const getOverallProgress = () => {
      if (formData.value.evidence.length === 0) return 0
      
      const totalProgress = formData.value.evidence.reduce((sum, file) => {
        return sum + (file.progress || 0)
      }, 0)
      
      return Math.round(totalProgress / formData.value.evidence.length)
    }

    // Legacy upload method - kept for backward compatibility but not used in new evidence system
    const uploadFiles = async (files) => {
      // Check consent before proceeding with event evidence upload
      try {
        const consentService = (await import('@/services/consentService.js')).default;
        const { CONSENT_ACTIONS } = await import('@/utils/consentManager.js');
        
        const canProceed = await consentService.checkAndRequestConsent(
          CONSENT_ACTIONS.UPLOAD_EVENT
        );
        
        // If user declined consent, stop here
        if (!canProceed) {
          console.log('Event evidence upload cancelled by user (consent declined)');
          return;
        }
      } catch (consentError) {
        console.error('Error checking consent:', consentError);
        // Continue with upload if consent check fails
      }

      const userId = localStorage.getItem('user_id')
      if (!userId) {
        PopupService.error('User ID not found. Please log in again.', 'Authentication Error')
        return
      }

      uploadingFiles.value = true
      const uploadPromises = []

      for (const file of files) {
        // Validate file size (10MB limit)
        if (file.size > 10 * 1024 * 1024) {
          PopupService.warning(`File "${file.name}" is too large. Maximum size is 10MB.`, 'File Size Error')
          continue
        }

        // Validate file type
        const allowedTypes = ['application/pdf', 'text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
        if (!allowedTypes.includes(file.type)) {
          PopupService.warning(`File "${file.name}" has an unsupported format. Supported formats: PDF, CSV, XLSX, DOC, TXT`, 'File Type Error')
          continue
        }

        // Add file to evidence list immediately
        const fileId = Date.now() + Math.random()
        const fileData = {
          id: fileId,
          name: file.name,
          size: file.size,
          type: file.type,
          status: 'uploading',
          progress: 0
        }
        formData.value.evidence.push(fileData)
        uploadProgress.value[fileId] = 0

        // Upload file
        const uploadPromise = uploadSingleFile(file, userId, fileId)
        uploadPromises.push(uploadPromise)
      }

      try {
        await Promise.all(uploadPromises)
        PopupService.success('All files uploaded successfully!', 'Upload Complete')
      } catch (error) {
        console.error('Error uploading files:', error)
        PopupService.error('Some files failed to upload. Please try again.', 'Upload Error')
      } finally {
        uploadingFiles.value = false
      }
    }

    const uploadSingleFile = async (file, userId, fileId) => {
      try {
        const response = await s3Service.uploadFile(file, userId)
        
        if (response.data.success) {
          // Update file data with S3 information
          const fileIndex = formData.value.evidence.findIndex(f => f.id === fileId)
          console.log('DEBUG: Upload successful, updating file at index:', fileIndex)
          console.log('DEBUG: S3 response data:', response.data)
          
          if (fileIndex !== -1) {
            formData.value.evidence[fileIndex] = {
              ...formData.value.evidence[fileIndex],
              status: 'uploaded',
              progress: 100,
              s3Key: response.data.s3_key,
              s3Url: response.data.s3_url,
              storedName: response.data.stored_name
            }
            console.log('DEBUG: Updated file data:', formData.value.evidence[fileIndex])
          } else {
            console.log('DEBUG: File index not found for fileId:', fileId)
          }
          delete uploadProgress.value[fileId]
        } else {
          throw new Error(response.data.message || 'Upload failed')
        }
      } catch (error) {
        console.error('Error uploading file:', error)
        // Update file status to error
        const fileIndex = formData.value.evidence.findIndex(f => f.id === fileId)
        if (fileIndex !== -1) {
          formData.value.evidence[fileIndex].status = 'error'
          formData.value.evidence[fileIndex].error = error.message
        }
        delete uploadProgress.value[fileId]
        throw error
      }
    }

    const removeFile = (fileId) => {
      const fileIndex = formData.value.evidence.findIndex(f => f.id === fileId)
      if (fileIndex !== -1) {
        formData.value.evidence.splice(fileIndex, 1)
        delete uploadProgress.value[fileId]
      }
    }


    // Helper functions for file type detection and formatting
    const isPdfFile = (fileType) => {
      return fileType === 'application/pdf' || fileType?.toLowerCase().includes('pdf')
    }

    const isExcelFile = (fileType) => {
      return fileType === 'application/vnd.ms-excel' || 
             fileType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
             fileType?.toLowerCase().includes('excel') ||
             fileType?.toLowerCase().includes('spreadsheet')
    }

    const isWordFile = (fileType) => {
      return fileType === 'application/msword' || 
             fileType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
             fileType?.toLowerCase().includes('word') ||
             fileType?.toLowerCase().includes('document')
    }

    const getFileTypeClass = (fileType) => {
      if (isPdfFile(fileType)) return 'file-type-pdf'
      if (isExcelFile(fileType)) return 'file-type-excel'
      if (isWordFile(fileType)) return 'file-type-word'
      if (fileType?.toLowerCase().includes('text')) return 'file-type-text'
      return 'file-type-default'
    }

    const getFileTypeName = (fileType) => {
      if (isPdfFile(fileType)) return 'PDF'
      if (isExcelFile(fileType)) return 'Excel'
      if (isWordFile(fileType)) return 'Word'
      if (fileType?.toLowerCase().includes('text')) return 'Text'
      if (fileType?.toLowerCase().includes('csv')) return 'CSV'
      return 'Document'
    }

    const formatFileSize = (bytes) => {
      if (!bytes || bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const previewFile = (file) => {
      if (isPdfFile(file.type) && file.s3Url) {
        // Open PDF in new tab for preview
        window.open(file.s3Url, '_blank')
      } else {
        PopupService.info('Preview not available for this file type', 'Preview')
      }
    }
    
    // Evidence attachment methods
    const showEvidenceOptionsPanel = () => {
      showEvidenceOptions.value = true
      uploadError.value = ''
    }
    
    const goBackToInitial = () => {
      showEvidenceOptions.value = true
      showUploadArea.value = false
      showLinkArea.value = false
      uploadError.value = ''
      uploadSuccess.value = false
    }
    
    const goBackToOptions = () => {
      showEvidenceOptions.value = true
      showUploadArea.value = false
      showLinkArea.value = false
      uploadError.value = ''
      uploadSuccess.value = false
    }
    
    const selectUploadOption = () => {
      showEvidenceOptions.value = false
      showUploadArea.value = true
      showLinkArea.value = false
    }
    
    const selectLinkOption = () => {
      showEvidenceOptions.value = false
      showUploadArea.value = false
      showLinkArea.value = true
      // Load events when link area is opened
      fetchAllEvents()
    }
    
    const triggerFileUpload = () => {
      if (fileInput.value) {
        fileInput.value.click()
      }
    }
    
    const removeSelectedFile = (index) => {
      selectedFiles.value.splice(index, 1)
    }
    
    const clearSelectedFiles = () => {
      selectedFiles.value = []
    }
    
    const uploadSelectedFiles = async () => {
      if (selectedFiles.value.length === 0) {
        uploadError.value = 'Please select files to upload.'
        return
      }

      // Check consent before proceeding with event evidence upload
      try {
        const consentService = (await import('@/services/consentService.js')).default;
        const { CONSENT_ACTIONS } = await import('@/utils/consentManager.js');
        
        const canProceed = await consentService.checkAndRequestConsent(
          CONSENT_ACTIONS.UPLOAD_EVENT
        );
        
        // If user declined consent, stop here
        if (!canProceed) {
          console.log('Event evidence upload cancelled by user (consent declined)');
          return;
        }
      } catch (consentError) {
        console.error('Error checking consent:', consentError);
        // Continue with upload if consent check fails
      }

      uploadingFiles.value = true
      uploadProgress.value = 0
      uploadError.value = ''
      uploadSuccess.value = false

      try {
        const uploadedFiles = []
        const totalFiles = selectedFiles.value.length
        
        // Upload files one by one
        for (let i = 0; i < selectedFiles.value.length; i++) {
          const file = selectedFiles.value[i]
          
          // Create form data for file upload
          const formData = new FormData()
          formData.append('file', file)
          formData.append('user_id', localStorage.getItem('user_id') || 'temp')
          
          try {
            // Make API call to upload file
            const response = await s3Service.uploadFile(file, localStorage.getItem('user_id'))
            
            if (response.data.success) {
              uploadedFiles.push({
                id: Date.now() + Math.random(),
                name: file.name,
                size: file.size,
                type: file.type,
                status: 'uploaded',
                progress: 100,
                s3Key: response.data.s3_key,
                s3Url: response.data.s3_url,
                storedName: response.data.stored_name
              })
            } else {
              throw new Error(response.data.message || `Failed to upload ${file.name}`)
            }
          } catch (fileError) {
            console.error(`Error uploading ${file.name}:`, fileError)
            uploadError.value = `Failed to upload ${file.name}: ${fileError.message}`
            break
          }
          
          // Update progress
          uploadProgress.value = Math.round(((i + 1) / totalFiles) * 100)
        }
        
        if (uploadedFiles.length === selectedFiles.value.length) {
          // All files uploaded successfully
          formData.value.evidence.push(...uploadedFiles)
          uploadSuccess.value = true
          selectedFiles.value = []
          
          setTimeout(() => {
            uploadSuccess.value = false
            goBackToInitial()
          }, 2000)
          
          PopupService.success(`${uploadedFiles.length} file(s) uploaded successfully!`, 'Upload Complete')
        }
      } catch (error) {
        console.error('Error uploading files:', error)
        uploadError.value = 'Failed to upload files. Please try again.'
      } finally {
        uploadingFiles.value = false
      }
    }
    
    // Link evidence methods
    const setActiveFilter = (filter) => {
      activeFilter.value = filter
      if (filter !== 'All') {
        fetchEventsByType(filter)
      }
    }
    
    const fetchAllEvents = async () => {
      loadingEvents.value = true
      eventsError.value = ''
      
      try {
        // Fetch events from different sources
        await Promise.all([
          fetchEventsByType('Riskavaire'),
          fetchEventsByType('Integrations'),
          fetchEventsByType('Document Handling')
        ])
      } catch (error) {
        console.error('Error fetching events:', error)
        eventsError.value = 'Failed to load events. Please try again.'
      } finally {
        loadingEvents.value = false
      }
    }
    
    const fetchEventsByType = async (type) => {
      try {
        let response
        
        if (type === 'Riskavaire') {
          response = await eventService.getEvents()
          if (response.data.success) {
            riskavaireEvents.value = response.data.events.map(event => ({
              ...event,
              source: 'Riskavaire'
            }))
          }
        } else if (type === 'Integrations') {
          // Fetch integration events (Jira, etc.)
          response = await eventService.getIntegrationEvents()
          if (response.data.success) {
            integrationEvents.value = response.data.events.map(event => ({
              ...event,
              source: event.source || 'Integration'
            }))
          }
        } else if (type === 'Document Handling') {
          // Fetch document handling events
          response = await eventService.getDocumentHandlingEvents()
          if (response.data.success) {
            documentHandlingEvents.value = response.data.events.map(event => ({
              ...event,
              source: 'Document Handling System'
            }))
          }
        }
      } catch (error) {
        console.error(`Error fetching ${type} events:`, error)
        // Don't set error here as it's handled in fetchAllEvents
      }
    }
    
    const isEventSelected = (event) => {
      return selectedEvents.value.some(selectedEvent => selectedEvent.id === event.id)
    }
    
    const selectEvent = (event) => {
      const index = selectedEvents.value.findIndex(selectedEvent => selectedEvent.id === event.id)
      if (index > -1) {
        selectedEvents.value.splice(index, 1)
      } else {
        selectedEvents.value.push(event)
      }
    }
    
    const linkSelectedEvents = async () => {
      if (selectedEvents.value.length === 0) {
        uploadError.value = 'Please select events to link.'
        return
      }
      
      uploadingFiles.value = true
      uploadError.value = ''
      
      try {
        // Transform linked events to match the uploaded files format
        const linkedEventsAsFiles = selectedEvents.value.map(event => ({
          id: Date.now() + Math.random(),
          name: `${event.title} (${event.source})`,
          size: 0,
          type: 'linked_evidence',
          status: 'uploaded',
          progress: 100,
          s3Key: `#linked-event-${event.id}`,
          s3Url: `#linked-event-${event.id}`,
          storedName: `${event.title} (${event.source})`,
          linkedEvent: event
        }))
        
        // Add linked events to evidence
        formData.value.evidence.push(...linkedEventsAsFiles)
        
        uploadSuccess.value = true
        selectedEvents.value = []
        uploadProgress.value = 100
        
        setTimeout(() => {
          uploadSuccess.value = false
          goBackToInitial()
        }, 2000)
        
        PopupService.success(`${linkedEventsAsFiles.length} event(s) linked successfully!`, 'Link Complete')
      } catch (error) {
        console.error('Error linking events:', error)
        uploadError.value = 'Failed to link selected events. Please try again.'
      } finally {
        uploadingFiles.value = false
      }
    }

    // Watchers for dynamic record fetching
    watch(() => formData.value.frameworkId, (newFrameworkId) => {
      if (newFrameworkId) {
        fetchRecords(newFrameworkId, formData.value.module || '')
      }
    })

    watch(() => formData.value.module, (newModule) => {
      if (formData.value.frameworkId) {
        fetchRecords(formData.value.frameworkId, newModule || '')
      }
    })

    // Function to handle event type selection and load sub-event types
    const handleEventTypeChange = () => {
      const selectedEventType = eventTypes.value.find(et => et.eventtype_id === formData.value.eventTypeId)
      if (selectedEventType) {
        // Clear previous sub-event type selection
        formData.value.subEventTypeId = ''
        
        // Load sub-event types if available
        if (selectedEventType.eventSubtype) {
          if (Array.isArray(selectedEventType.eventSubtype)) {
            // Handle array format: ["Type 1", "Type 2", ...]
            subEventTypes.value = selectedEventType.eventSubtype.map((subType, index) => ({
              id: index,
              name: subType
            }))
          } else if (typeof selectedEventType.eventSubtype === 'object') {
            // Handle object format: {"key1": [...], "key2": [...], ...}
            const subTypeKeys = Object.keys(selectedEventType.eventSubtype)
            
            // Create a mapping for better display names
            const displayNameMap = {
              'risk_register_updates': 'Risk Register Updates',
              'formal_risk_assessments': 'Formal Risk Assessments',
              'documented_risk_treatment_plans': 'Documented Risk Treatment Plans',
              'approval_records_of_risk_acceptance_or_residual_risk': 'Approval Records Of Risk Acceptance Or Residual Risk',
              'isms_policy_review': 'ISMS Policy Review',
              'management_review': 'Management Review Meeting',
              'resource_allocation': 'Resource Allocation Review',
              'performance_monitoring': 'Performance Monitoring',
              'continuous_improvement': 'Continuous Improvement Initiative'
            }
            
            subEventTypes.value = subTypeKeys.map((key, index) => ({
              id: index,
              name: displayNameMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) // Use mapping or fallback to Title Case
            }))
          } else {
            subEventTypes.value = []
          }
        } else {
          subEventTypes.value = []
        }
      }
    }

    // Watcher for event type selection
    watch(() => formData.value.eventTypeId, (newEventTypeId) => {
      if (newEventTypeId === 'create_new') {
        openCreateEventTypeModal()
      } else if (newEventTypeId) {
        handleEventTypeChange()
      } else {
        // Clear sub-event types when no event type is selected
        subEventTypes.value = []
        formData.value.subEventTypeId = ''
      }
    })

    // Watcher for module selection
    watch(() => formData.value.module, (newModule) => {
      if (newModule === 'create_new') {
        openCreateModuleModal()
      }
    })

    // Function to process prefilled data after frameworks are loaded
    const processPrefilledData = () => {
      // Check for integration event data
      const integrationData = sessionStorage.getItem('integrationEventData')
      if (integrationData) {
        try {
          const data = JSON.parse(integrationData)
          
          // Pre-fill form with integration data
          if (data.title) {
            formData.value.title = data.title
          }
          if (data.description) {
            formData.value.description = data.description
          }
          if (data.framework) {
            formData.value.framework = data.framework
            // Find framework ID
            const selectedFramework = frameworks.value.find(fw => fw.FrameworkName === data.framework)
            if (selectedFramework) {
              formData.value.frameworkId = selectedFramework.FrameworkId
              console.log('Integration: Set frameworkId to:', formData.value.frameworkId)
            } else {
              console.log('Integration: Framework not found in frameworks array:', data.framework, frameworks.value)
            }
          }
          if (data.module) {
            formData.value.module = data.module
          }
          if (data.category) {
            formData.value.category = data.category
          }
          if (data.owner) {
            formData.value.owner = data.owner
          }
          if (data.reviewer) {
            formData.value.reviewer = data.reviewer
          }
          if (data.priority) {
            formData.value.priority = data.priority
          }
          if (data.status) {
            formData.value.status = data.status
          }
          
          // Fetch records if both framework and module are available
          if (formData.value.frameworkId && formData.value.module) {
            console.log('Integration: Fetching records for frameworkId:', formData.value.frameworkId, 'module:', formData.value.module)
            fetchRecords(formData.value.frameworkId, formData.value.module)
          } else {
            console.log('Integration: Cannot fetch records - frameworkId:', formData.value.frameworkId, 'module:', formData.value.module)
          }
          
          // Set linked record information for Jira
          if (data.source === 'Jira' && data.rawData) {
            formData.value.linkedRecordType = 'Jira Issue'
            formData.value.linkedRecordId = data.rawData.issue_key || data.rawData.id
            formData.value.linkedRecordName = data.rawData.issue_key || data.rawData.summary
          }
          
          // Store popup data for Source Information section
          if (data.popupData) {
            formData.value.sourceInformation = data.popupData
          }
          
          // Set source and timestamp for display
          formData.value.source = data.source || 'Unknown'
          formData.value.sourceTimestamp = data.timestamp || new Date().toISOString()
          
          // Clear the session storage after using it
          sessionStorage.removeItem('integrationEventData')
          
          console.log('Pre-filled form with integration data:', data)
        } catch (error) {
          console.error('Error parsing integration data:', error)
        }
      }
      
      // Check for RiskaVaire event data
      const riskavaireData = sessionStorage.getItem('riskavaireEventData')
      if (riskavaireData) {
        try {
          const data = JSON.parse(riskavaireData)
          
          // Pre-fill form with RiskaVaire data
          if (data.title) {
            formData.value.title = data.title
          }
          if (data.description) {
            formData.value.description = data.description
          }
          if (data.framework) {
            formData.value.framework = data.framework
            // Find framework ID
            const selectedFramework = frameworks.value.find(fw => fw.FrameworkName === data.framework)
            if (selectedFramework) {
              formData.value.frameworkId = selectedFramework.FrameworkId
              console.log('RiskaVaire: Set frameworkId to:', formData.value.frameworkId)
            } else {
              console.log('RiskaVaire: Framework not found in frameworks array:', data.framework, frameworks.value)
            }
          }
          if (data.module) {
            formData.value.module = data.module
          }
          if (data.category) {
            formData.value.category = data.category
          }
          if (data.owner) {
            formData.value.owner = data.owner
          }
          if (data.reviewer) {
            formData.value.reviewer = data.reviewer
          }
          if (data.priority) {
            formData.value.priority = data.priority
          }
          if (data.status) {
            formData.value.status = data.status
          }
          
          // Fetch records if both framework and module are available
          if (formData.value.frameworkId && formData.value.module) {
            console.log('RiskaVaire: Fetching records for frameworkId:', formData.value.frameworkId, 'module:', formData.value.module)
            fetchRecords(formData.value.frameworkId, formData.value.module)
          } else {
            console.log('RiskaVaire: Cannot fetch records - frameworkId:', formData.value.frameworkId, 'module:', formData.value.module)
          }
          
          // Set linked record information for RiskaVaire
          if (data.linkedRecordType && data.linkedRecordId) {
            formData.value.linkedRecordType = data.linkedRecordType
            formData.value.linkedRecordId = data.linkedRecordId
            formData.value.linkedRecordName = data.linkedRecordName || data.linkedRecordId
          }
          
          // Store popup data for Source Information section
          if (data.popupData) {
            formData.value.sourceInformation = data.popupData
          }
          
          // Set source and timestamp for display
          formData.value.source = data.source || 'RiskaVaire Module'
          formData.value.sourceTimestamp = data.timestamp || new Date().toISOString()
          
          // Clear the session storage after using it
          sessionStorage.removeItem('riskavaireEventData')
          
          console.log('Pre-filled form with RiskaVaire data:', data)
        } catch (error) {
          console.error('Error parsing RiskaVaire data:', error)
        }
      }
    }

    // Check permissions and fetch data on component mount
    onMounted(async () => {
      // Check if user has permission to create events
      try {
        const response = await eventService.getUserEventPermissions()
        if (response.data.success) {
          const permissions = response.data.permissions
          // Check if user has create permission or is admin
          if (!permissions.create_event && !permissions.is_admin) {
            AccessUtils.showAccessDenied('Event Management - Create Event', 'You don\'t have permission to create events. Required permission: event.create_event')
            return
          }
        } else {
          // If permissions API fails, show access denied
          AccessUtils.showAccessDenied('Event Management - Create Event', 'Unable to verify permissions. Please contact your administrator.')
          return
        }
      } catch (error) {
        console.error('Error checking event permissions:', error)
        // If permissions check fails, show access denied
        AccessUtils.showAccessDenied('Event Management - Create Event', 'Unable to verify permissions. Please contact your administrator.')
        return
      }
      
      await fetchFrameworks()
      await fetchModules()
      fetchTemplates()
      fetchCurrentUser()
      fetchReviewers()
      
      // Process prefilled data after frameworks are loaded
      processPrefilledData()
      
      // Check for edit event data
      const editEventData = sessionStorage.getItem('editEventData')
      if (editEventData) {
        try {
          const data = JSON.parse(editEventData)
          
          // Pre-fill form with edit data
          if (data.title) {
            formData.value.title = data.title
          }
          if (data.description) {
            formData.value.description = data.description
          }
          if (data.framework) {
            formData.value.framework = data.framework
            // Find framework ID
            const selectedFramework = frameworks.value.find(fw => fw.FrameworkName === data.framework)
            if (selectedFramework) {
              formData.value.frameworkId = selectedFramework.FrameworkId
              console.log('Edit: Set frameworkId to:', formData.value.frameworkId)
            } else {
              console.log('Edit: Framework not found in frameworks array:', data.framework, frameworks.value)
            }
          }
          if (data.module) {
            formData.value.module = data.module
          }
          if (data.category) {
            formData.value.category = data.category
          }
          if (data.owner) {
            formData.value.owner = data.owner
          }
          if (data.reviewer) {
            formData.value.reviewer = data.reviewer
          }
          if (data.recurrence) {
            formData.value.recurrence = data.recurrence
          }
          if (data.frequency) {
            formData.value.frequency = data.frequency
          }
          if (data.startDate) {
            formData.value.startDate = data.startDate
          }
          if (data.endDate) {
            formData.value.endDate = data.endDate
          }
          
          // Fetch records if both framework and module are available
          if (formData.value.frameworkId && formData.value.module) {
            console.log('Edit: Fetching records for frameworkId:', formData.value.frameworkId, 'module:', formData.value.module)
            fetchRecords(formData.value.frameworkId, formData.value.module)
          } else {
            console.log('Edit: Cannot fetch records - frameworkId:', formData.value.frameworkId, 'module:', formData.value.module)
          }
          
          // Set edit mode flag
          formData.value.isEdit = data.isEdit
          formData.value.editEventId = data.id
          
          // Handle existing evidence data
          if (data.evidence && data.evidence.length > 0) {
            console.log('Edit: Processing existing evidence:', data.evidence)
            // Convert evidence objects to the format expected by the form
            formData.value.evidence = data.evidence.map((ev, index) => ({
              id: `existing-${index}`,
              name: ev.fileName || `Evidence File ${index + 1}`,
              size: ev.size || 'Unknown',
              type: 'application/octet-stream',
              status: 'uploaded',
              progress: 100,
              s3Key: ev.s3_url ? decodeURIComponent(ev.s3_url.split('/').pop()) : null,
              s3Url: ev.url || ev.s3_url,
              storedName: ev.fileName || `Evidence File ${index + 1}`,
              uploadedAt: ev.uploadDate || new Date().toISOString()
            }))
            console.log('Edit: Processed evidence for form:', formData.value.evidence)
          } else if (data.evidence_string) {
            console.log('Edit: Processing evidence string:', data.evidence_string)
            // Convert evidence string to evidence objects
            const evidenceUrls = data.evidence_string.split(';').filter(url => url.trim())
            formData.value.evidence = evidenceUrls.map((url, index) => {
              const filename = url.split('/').pop() || `Evidence File ${index + 1}`
              return {
                id: `existing-${index}`,
                name: filename,
                size: 'Unknown',
                type: 'application/octet-stream',
                status: 'uploaded',
                progress: 100,
                s3Key: decodeURIComponent(url.split('/').pop()),
                s3Url: url,
                storedName: filename,
                uploadedAt: new Date().toISOString()
              }
            })
            console.log('Edit: Processed evidence from string:', formData.value.evidence)
          }
          
          // Clear the session storage after using it
          sessionStorage.removeItem('editEventData')
          
          console.log('Pre-filled form with edit data:', data)
        } catch (error) {
          console.error('Error parsing edit data:', error)
        }
      }
    })

    return {
      currentStep,
      formData,
      steps,
      frameworks,
      loadingFrameworks,
      frameworksError,
      modules,
      loadingModules,
      modulesError,
      records,
      loadingRecords,
      recordsError,
      eventTypes,
      loadingEventTypes,
      eventTypesError,
      subEventTypes,
      loadingSubEventTypes,
      templates,
      loadingTemplates,
      currentUser,
      loadingCurrentUser,
      reviewers,
      loadingReviewers,
      uploadingFiles,
      uploadProgress,
      isDragOver,
      dynamicFields,
      loadingDynamicFields,
      dynamicFieldsError,
      RECURRENCE_FREQUENCIES,
      handleNext,
      handlePrevious,
      handleSubmit,
      generateEventId,
      getEventTypeName,
      getSubEventTypeName,
      fetchFrameworks,
      fetchModules,
      fetchEventTypes,
      fetchRecords,
      fetchTemplates,
      fetchCurrentUser,
      fetchReviewers,
      fetchDynamicFields,
      handleFrameworkChange,
      handleRecordChange,
      handleReviewerChange,
      handleEventTypeChange,
      useTemplate,
      addAnotherRecord,
      removeAdditionalRecord,
      handleAdditionalRecordFrameworkChange,
      handleAdditionalRecordModuleChange,
      handleAdditionalRecordChange,
      showSourceDetailsPopup,
      showSourcePopup,
      closeSourcePopup,
      getSourceStatusBadgeClass,
      handleFileSelect,
      handleDrop,
      handleDragOver,
      handleDragLeave,
      openFileDialog,
      openFolderDialog,
      handleFolderSelect,
      getOverallProgress,
      uploadFiles,
      removeFile,
      // File helper functions
      isPdfFile,
      isExcelFile,
      isWordFile,
      getFileTypeClass,
      getFileTypeName,
      formatFileSize,
      previewFile,
      // Evidence attachment functions
      showEvidenceOptions,
      showUploadArea,
      showLinkArea,
      selectedFiles,
      uploadSuccess,
      uploadError,
      searchQuery,
      filteredEvents,
      loadingEvents,
      eventsError,
      activeFilter,
      selectedEvents,
      showEvidenceOptionsPanel,
      goBackToInitial,
      goBackToOptions,
      selectUploadOption,
      selectLinkOption,
      triggerFileUpload,
      removeSelectedFile,
      clearSelectedFiles,
      uploadSelectedFiles,
      setActiveFilter,
      fetchAllEvents,
      isEventSelected,
      selectEvent,
      linkSelectedEvents,
      fileInput,
      // Create Event Type Modal functions
      showCreateEventTypeModal,
      newEventTypeName,
      newEventTypeError,
      creatingEventType,
      openCreateEventTypeModal,
      closeCreateEventTypeModal,
      clearNewEventTypeError,
      createNewEventType,
      // Create Module Modal functions
      showCreateModuleModal,
      newModuleName,
      newModuleError,
      creatingModule,
      openCreateModuleModal,
      closeCreateModuleModal,
      clearNewModuleError,
      createNewModule
    }
  }
}
</script>

<style>
/* Event Creation Container */
.event-creation-container {
  padding: 24px;
  padding-top:40px;
  background: white;
  min-height: 100vh;
}


.event-creation-wrapper {
  max-width: 1200px;
  margin: 0 auto;
}

/* Event Creation Header */
.event-creation-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
  padding: 24px 32px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border-radius: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
}

.event-creation-title-section {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.event-creation-title-content {
  flex: 1;
}

.event-creation-title {
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px 0;
  line-height: 1.2;
}

.event-creation-subtitle {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
  font-weight: 500;
}

.event-creation-back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  margin-left:-10px;
  background: #ffffff;
  color: #374151;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.3s ease;

}

.event-creation-back-btn:hover {
  background: #f9fafb;
  border-color: #d1d5db;
  transform: translateY(-2px);
  color: #1f2937;
}

.event-creation-back-icon {
  width: 16px;
  height: 16px;
}

/* Event Creation Progress */
.event-creation-steps-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  margin-bottom: 32px;
}

.event-creation-step {
  display: flex;
  align-items: center;
  flex: 1;
  position: relative;
}

.event-creation-step-circle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 3px solid;
  font-weight: 700;
  font-size: 1.1rem;
  transition: all 0.3s ease;
  position: relative;
  z-index: 2;
}

.event-creation-step-active {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-color: #2563eb;
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.event-creation-step-inactive {
  background: #ffffff;
  border-color: #d1d5db;
  color: #9ca3af;
}

.event-creation-step-check {
  display: flex;
  align-items: center;
  justify-content: center;
}

.event-creation-step-check-icon {
  width: 20px;
  height: 20px;
}

.event-creation-step-number {
  font-weight: 700;
}

.event-creation-step-content {
  margin-left: 16px;
  flex: 1;
}

.event-creation-step-title {
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0 0 4px 0;
  transition: color 0.3s ease;
}

.event-creation-step-title-active {
  color: #1f2937;
}

.event-creation-step-title-inactive {
  color: #9ca3af;
}

.event-creation-step-description {
  font-size: 0.8rem;
  color: #6b7280;
  margin: 0;
  line-height: 1.4;
}

.event-creation-step-connector {
  flex: 1;
  height: 3px;
  margin: 0 16px;
  border-radius: 2px;
  transition: all 0.3s ease;
}

.event-creation-step-connector-active {
  background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
}

.event-creation-step-connector-inactive {
  background: #e5e7eb;
}

/* Event Creation Form */
.event-creation-form {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
  padding: 32px;
  margin-bottom: 32px;
}

/* Integration Banner */
.event-creation-integration-banner {
  margin-bottom: 24px;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border: 1px solid #93c5fd;
  border-radius: 12px;
  padding: 20px;
}

.event-creation-integration-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.event-creation-integration-icon {
  width: 20px;
  height: 20px;
  color: #3b82f6;
  flex-shrink: 0;
}

.event-creation-integration-text {
  flex: 1;
}

.event-creation-integration-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1e40af;
  margin: 0 0 4px 0;
}

.event-creation-integration-subtitle {
  font-size: 0.85rem;
  color: #1d4ed8;
  margin: 0;
  line-height: 1.4;
}


/* Template Indicator */
.event-creation-template-indicator {
  margin-bottom: 24px;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border: 1px solid #93c5fd;
  border-radius: 12px;
  padding: 20px;
}

.event-creation-template-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.event-creation-template-icon {
  width: 20px;
  height: 20px;
  color: #3b82f6;
  flex-shrink: 0;
}

.event-creation-template-text {
  flex: 1;
}

.event-creation-template-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1e40af;
  margin: 0 0 4px 0;
}

.event-creation-template-subtitle {
  font-size: 0.85rem;
  color: #1d4ed8;
  margin: 0;
  line-height: 1.4;
}

/* Step 2 Specific Styles */
.event-creation-step-2 {
  padding: 0;
}

/* Form Grid */
.event-creation-form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.event-creation-form-group-full {
  grid-column: 1 / -1;
}

.event-creation-form-group {
  display: flex;
  flex-direction: column;
}

.event-creation-form-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  line-height: 1.4;
}

.event-creation-form-required {
  color: #dc2626;
  font-weight: 700;
}

.event-creation-form-hint {
  font-size: 0.8rem;
  color: #9ca3af;
  font-weight: 400;
  margin-left: 4px;
}

.event-creation-form-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  background: #ffffff;
  font-size: 0.9rem;
  color: #374151;
  transition: all 0.3s ease;
  font-family: inherit;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.event-creation-form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.event-creation-form-input-disabled {
  background: #f9fafb;
  color: #9ca3af;
  cursor: not-allowed;
  border-color: #d1d5db;
}

.event-creation-form-input-error {
  border-color: #dc2626;
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1);
}

.event-creation-form-input-error:focus {
  border-color: #dc2626;
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1);
}

.event-creation-form-textarea {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  background: #ffffff;
  font-size: 0.9rem;
  color: #374151;
  transition: all 0.3s ease;
  font-family: inherit;
  resize: vertical;
  min-height: 100px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.event-creation-form-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.event-creation-form-select {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  background: #ffffff;
  color: #374151;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  cursor: pointer;
  font-family: inherit;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.event-creation-form-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.event-creation-form-select:disabled {
  background: #f9fafb;
  color: #9ca3af;
  cursor: not-allowed;
}

.event-creation-form-error {
  margin-top: 8px;
  font-size: 0.85rem;
  color: #dc2626;
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.event-creation-form-error-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.event-creation-form-retry {
  color: #3b82f6;
  text-decoration: underline;
  cursor: pointer;
  font-weight: 500;
}

.event-creation-form-retry:hover {
  color: #2563eb;
}

/* Section Styles */
.event-creation-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 2px solid #e5e7eb;
}

.event-creation-section-header {
  margin-bottom: 20px;
}

.event-creation-section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #374151;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.event-creation-section-title::before {
  content: '';
  width: 4px;
  height: 20px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-radius: 2px;
}

/* Radio Button Styles */
.event-creation-radio-group {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
}

.event-creation-radio-option {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.event-creation-radio-option:hover {
  background: #f8f9fa;
}

.event-creation-radio-input {
  width: 18px;
  height: 18px;
  accent-color: #3b82f6;
  cursor: pointer;
}

.event-creation-radio-label {
  font-size: 0.9rem;
  font-weight: 500;
  color: #374151;
  cursor: pointer;
}

/* Checkbox Styles */
.event-creation-checkbox-group {
  margin-bottom: 20px;
}

.event-creation-checkbox-option {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.event-creation-checkbox-option:hover {
  background: #f8f9fa;
}

.event-creation-checkbox-input {
  width: 18px;
  height: 18px;
  accent-color: #3b82f6;
  cursor: pointer;
}

.event-creation-checkbox-label {
  font-size: 0.9rem;
  font-weight: 500;
  color: #374151;
  cursor: pointer;
}

/* Recurring Options */
.event-creation-recurring-options {
  margin-top: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

/* Template Info */
.event-creation-template-info {
  margin-top: 16px;
  padding: 16px;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border: 1px solid #93c5fd;
  border-radius: 12px;
}

.event-creation-template-info-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.event-creation-template-info-icon {
  width: 20px;
  height: 20px;
  color: #1e40af;
  flex-shrink: 0;
  margin-top: 2px;
}

.event-creation-template-info-text {
  flex: 1;
  font-size: 0.9rem;
  color: #1e40af;
  line-height: 1.5;
}

/* Add Record Button */
.event-creation-add-record-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: #ffffff;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  color: #374151;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.event-creation-add-record-btn:hover {
  background: #f9fafb;
  border-color: #3b82f6;
  color: #3b82f6;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.event-creation-add-record-icon {
  width: 16px;
  height: 16px;
}

.event-creation-add-record-badge {
  margin-left: 8px;
  padding: 4px 8px;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  color: #1e40af;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

/* Additional Records */
.event-creation-additional-records {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 2px solid #e5e7eb;
}

.event-creation-additional-records-header {
  margin-bottom: 20px;
}

.event-creation-additional-records-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #374151;
  margin: 0;
}

.event-creation-additional-record {
  background: #f8f9fa;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.event-creation-additional-record:last-child {
  margin-bottom: 0;
}

.event-creation-additional-record-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.event-creation-additional-record-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #374151;
  margin: 0;
}

.event-creation-additional-record-remove-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #ffffff;
  border: 1px solid #fca5a5;
  border-radius: 8px;
  color: #dc2626;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.event-creation-additional-record-remove-btn:hover {
  background: #fef2f2;
  border-color: #f87171;
  color: #b91c1c;
  transform: translateY(-1px);
}

.event-creation-additional-record-remove-icon {
  width: 14px;
  height: 14px;
}

/* Step Content */
.event-creation-step-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Navigation */
.event-creation-navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  margin-bottom: 16px;
  padding-top: 20px;
  border-top: 2px solid #e5e7eb;
}

.event-creation-nav-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  height: 36px;
}

.event-creation-nav-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.event-creation-nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.event-creation-nav-btn-previous {
  background: #ffffff;
  border: 2px solid #e5e7eb;
  color: #374151;
}

.event-creation-nav-btn-previous:hover:not(:disabled) {
  background: #f9fafb;
  border-color: #d1d5db;
}

.event-creation-nav-btn-next,
.event-creation-nav-btn-submit {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff !important;
}

.event-creation-nav-btn-next:hover,
.event-creation-nav-btn-submit:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
}

.event-creation-nav-icon {
  width: 14px;
  height: 14px;
}

/* Source Information Section */
.event-creation-source-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 2px solid #e5e7eb;
}

.event-creation-source-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding: 20px 24px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #bae6fd;
  border-radius: 12px;
}

.event-creation-source-title-section {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.event-creation-source-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-radius: 12px;
  color: #ffffff;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.event-creation-source-icon svg {
  width: 24px;
  height: 24px;
}

.event-creation-source-title-content {
  flex: 1;
}

.event-creation-source-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e40af;
  margin: 0 0 4px 0;
  line-height: 1.3;
}

.event-creation-source-subtitle {
  font-size: 0.9rem;
  color: #1d4ed8;
  margin: 0;
  font-weight: 500;
}

.event-creation-source-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
  border: none;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.event-creation-source-btn:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
}

.event-creation-source-btn-icon {
  width: 16px;
  height: 16px;
}

.event-creation-source-content {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.event-creation-source-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.event-creation-source-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.event-creation-source-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0;
}

.event-creation-source-value {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.event-creation-source-value:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.event-creation-source-field-icon {
  width: 18px;
  height: 18px;
  color: #64748b;
  flex-shrink: 0;
}

.event-creation-source-value span {
  font-size: 0.95rem;
  font-weight: 500;
  color: #1e293b;
  flex: 1;
}

.event-creation-source-status-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Templates Section */
.event-creation-templates {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
  padding: 32px;
}

.event-creation-templates-header {
  margin-bottom: 24px;
}

.event-creation-templates-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.event-creation-templates-subtitle {
  font-size: 0.95rem;
  color: #6b7280;
  margin: 0;
}

.event-creation-templates-table-container {
  overflow-x: auto;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.event-creation-templates-table {
  width: 100%;
  border-collapse: collapse;
}

.event-creation-templates-header-row {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.event-creation-templates-th {
  padding: 16px 20px;
  text-align: left;
  font-size: 0.8rem;
  font-weight: 700;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid #e5e7eb;
}

.event-creation-templates-body {
  background: #ffffff;
}

.event-creation-templates-row {
  transition: all 0.2s ease;
  border-bottom: 1px solid #f3f4f6;
}

.event-creation-templates-row:hover {
  background: #f8f9fa;
}

.event-creation-templates-td {
  padding: 16px 20px;
  font-size: 0.9rem;
  color: #374151;
  vertical-align: middle;
}

.event-creation-templates-td-id {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-weight: 600;
  color: #3b82f6;
}

.event-creation-templates-loading,
.event-creation-templates-empty {
  background: #f8f9fa;
}

.event-creation-templates-loading-cell,
.event-creation-templates-empty-cell {
  padding: 40px 20px;
  text-align: center;
  font-size: 0.9rem;
  color: #6b7280;
  font-style: italic;
}

.event-creation-templates-use-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}

.event-creation-templates-use-btn:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

.event-creation-templates-use-icon {
  width: 12px;
  height: 12px;
}

/* Responsive Design */
@media (max-width: 768px) {
  .event-creation-container {
    padding: 16px;
  }
  
  .event-creation-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
    padding: 20px;
  }
  
  .event-creation-title {
    font-size: 1.5rem;
  }
  
  .event-creation-progress-track {
    flex-direction: column;
    gap: 16px;
  }
  
  .event-creation-step {
    flex-direction: column;
    text-align: center;
    gap: 8px;
  }
  
  .event-creation-step-content {
    margin-left: 0;
  }
  
  .event-creation-step-connector {
    display: none;
  }
  
  .event-creation-form {
    padding: 20px;
  }
  
  .event-creation-form-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .event-creation-navigation {
    flex-direction: column;
    gap: 12px;
  }
  
  .event-creation-nav-btn {
    width: 100%;
    justify-content: center;
  }
  
  .event-creation-templates {
    padding: 20px;
  }
  
  .event-creation-templates-table-container {
    font-size: 0.8rem;
  }
  
  .event-creation-templates-th,
  .event-creation-templates-td {
    padding: 12px 8px;
  }
}

/* Animations */
@keyframes event-creation-fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.event-creation-form {
  animation: event-creation-fadeIn 0.5s ease-out;
}

.event-creation-templates {
  animation: event-creation-fadeIn 0.6s ease-out;
}

/* Focus states for accessibility */
.event-creation-form-select:focus,
.event-creation-nav-btn:focus,
.event-creation-templates-use-btn:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Scrollbar styling */
.event-creation-templates-table-container::-webkit-scrollbar {
  height: 8px;
}

.event-creation-templates-table-container::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.event-creation-templates-table-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.event-creation-templates-table-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Source Details Popup Styles */
.source-details-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(8px);
  animation: source-details-fadeIn 0.3s ease-out;
}

.source-details-container {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15), 0 4px 10px rgba(0, 0, 0, 0.1);
  max-width: 600px;
  width: 85%;
  max-height: 80vh;
  overflow: hidden;
  margin: 20px;
  animation: source-details-slideIn 0.4s ease-out;
  display: flex;
  flex-direction: column;
}

.source-details-header {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 0;
  border-radius: 12px 12px 0 0;
  position: relative;
  overflow: hidden;
  border-bottom: 1px solid #cbd5e1;
}

.source-details-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.3) 0%, rgba(255, 255, 255, 0.1) 100%);
  pointer-events: none;
}

.source-details-header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  position: relative;
  z-index: 1;
}

.source-details-title-section {
  flex: 1;
}

.source-details-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 4px 0;
  line-height: 1.2;
}

.source-details-subtitle {
  font-size: 0.875rem;
  color: #64748b;
  margin: 0;
  font-weight: 500;
}

.source-details-close-btn {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  color: #64748b;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.source-details-close-btn:hover {
  background: #f1f5f9;
  border-color: #94a3b8;
  color: #475569;
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.source-details-close-icon {
  width: 20px;
  height: 20px;
  stroke-width: 2.5;
}

.source-details-content {
  padding: 24px;
  flex: 1;
  overflow-y: auto;
  background: #ffffff;
}

.source-details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.source-details-section {
  background: #f8fafc;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.source-details-section:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.source-details-details-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.source-details-detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.source-details-detail-label {
  font-size: 0.7rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}

.source-details-detail-value {
  font-size: 0.9rem;
  font-weight: 500;
  color: #1e293b;
  line-height: 1.4;
  word-break: break-word;
}

.source-details-status-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border: 1px solid transparent;
  max-width: fit-content;
}

.source-details-json-section {
  margin-top: 24px;
}

.source-details-json-label {
  display: block;
  font-size: 0.7rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.source-details-json-content {
  background: #f8fafc;
  border-radius: 8px;
  padding: 16px;
  font-size: 0.8rem;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
  color: #475569;
  overflow-x: auto;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  position: relative;
}

.source-details-json-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, #cbd5e1 50%, transparent 100%);
}

.source-details-json-content pre {
  margin: 0;
  line-height: 1.5;
  color: #475569;
}

.source-details-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 20px 24px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.source-details-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.source-details-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.source-details-btn:hover::before {
  left: 100%;
}

.source-details-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.source-details-btn-icon {
  width: 16px;
  height: 16px;
  stroke-width: 2.5;
}

.source-details-btn-close {
  background: #64748b;
  color: #ffffff;
}

.source-details-btn-close:hover {
  background: #475569;
}

/* Responsive Design for Source Details */
@media (max-width: 768px) {
  .source-details-container {
    width: 95%;
    margin: 10px;
    border-radius: 8px;
  }
  
  .source-details-header {
    border-radius: 8px 8px 0 0;
  }
  
  .source-details-header-content {
    padding: 16px 20px;
  }
  
  .source-details-title {
    font-size: 1.125rem;
  }
  
  .source-details-content {
    padding: 20px;
  }
  
  .source-details-grid {
    grid-template-columns: 1fr;
    gap: 16px;
    margin-bottom: 20px;
  }
  
  .source-details-section {
    padding: 16px;
  }
  
  .source-details-actions {
    padding: 16px 20px;
    flex-direction: column;
    gap: 12px;
  }
  
  .source-details-btn {
    width: 100%;
    justify-content: center;
    padding: 12px 20px;
  }
}

/* Animations for Source Details */
@keyframes source-details-fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes source-details-slideIn {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(30px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* Focus states for accessibility */
.source-details-close-btn:focus,
.source-details-btn:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Scrollbar styling for source details */
.source-details-content::-webkit-scrollbar,
.source-details-json-content::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.source-details-content::-webkit-scrollbar-track,
.source-details-json-content::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.source-details-content::-webkit-scrollbar-thumb,
.source-details-json-content::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.source-details-content::-webkit-scrollbar-thumb:hover,
.source-details-json-content::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Enhanced Upload Area Styles */
.group:hover .group-hover\:text-blue-500 {
  color: #3b82f6;
}

.group:hover .group-hover\:text-blue-600 {
  color: #2563eb;
}

/* Upload area drag and drop states */
.upload-area-dragover {
  border-color: #3b82f6 !important;
  background-color: #dbeafe !important;
  transform: scale(1.02);
}

/* File upload progress animations */
@keyframes upload-pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.upload-pulse {
  animation: upload-pulse 2s infinite;
}

/* Button hover effects */
.upload-btn-hover:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

/* File list animations */
.file-item-enter-active,
.file-item-leave-active {
  transition: all 0.3s ease;
}

/* Evidence Section Styles */
.evidence-section {
  margin-top: 2rem;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.evidence-header {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e2e8f0;
}

.evidence-title {
  display: flex;
  align-items: center;
  font-size: 1.125rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.evidence-icon {
  width: 1.25rem;
  height: 1.25rem;
  margin-right: 0.75rem;
  color: #3b82f6;
}

.evidence-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.evidence-item {
  background: white;
  border-radius: 12px;
  padding: 1.25rem;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.evidence-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  border-color: #3b82f6;
}

.evidence-item.uploading {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
}

.evidence-item.error {
  border-color: #ef4444;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
}

.evidence-item.uploaded {
  border-color: #10b981;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
}

.evidence-item-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.evidence-file-icon {
  flex-shrink: 0;
  width: 3rem;
  height: 3rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.file-icon-uploading {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  animation: pulse 2s infinite;
}

.file-icon-error {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.file-icon-success {
  color: white;
  font-weight: bold;
}

.file-type-pdf {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.file-type-excel {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.file-type-word {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
}

.file-type-text {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
}

.file-type-default {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
}

.evidence-file-icon svg {
  width: 1.5rem;
  height: 1.5rem;
}

.evidence-file-info {
  flex: 1;
  min-width: 0;
}

.evidence-file-name {
  font-size: 1rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.5rem;
  word-break: break-word;
}

.evidence-file-details {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  font-size: 0.875rem;
  color: #64748b;
}

.evidence-file-size {
  font-weight: 500;
}

.evidence-file-separator {
  color: #cbd5e1;
}

.evidence-file-type {
  background: #f1f5f9;
  color: #475569;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.evidence-status {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
}

.evidence-status.uploading {
  background: #dbeafe;
  color: #1e40af;
}

.evidence-status.error {
  background: #fee2e2;
  color: #dc2626;
}

.evidence-status.success {
  background: #dcfce7;
  color: #166534;
}

.evidence-status-icon {
  width: 0.875rem;
  height: 0.875rem;
}

.evidence-progress {
  margin-top: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.evidence-progress-bar {
  flex: 1;
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
}

.evidence-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.evidence-progress-text {
  font-size: 0.75rem;
  font-weight: 600;
  color: #3b82f6;
  min-width: 2.5rem;
  text-align: right;
}

.evidence-error-message {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #dc2626;
  background: #fef2f2;
  padding: 0.5rem;
  border-radius: 4px;
  border-left: 3px solid #ef4444;
}

.evidence-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.evidence-action-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  cursor: pointer;
}


.evidence-preview-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border-color: #10b981;
}

.evidence-preview-btn:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

.evidence-remove-btn {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border-color: #ef4444;
}

.evidence-remove-btn:hover {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}

.evidence-action-icon {
  width: 0.875rem;
  height: 0.875rem;
}

.evidence-action-text {
  font-weight: 500;
}

/* Responsive Design */
@media (max-width: 768px) {
  .evidence-item-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .evidence-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .evidence-action-btn {
    flex: 1;
    justify-content: center;
  }
  
  .evidence-file-details {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
}

/* Animation for new evidence items */
@keyframes evidence-slide-in {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.evidence-item {
  animation: evidence-slide-in 0.3s ease-out;
}

/* Evidence Upload Area Styles */
.evidence-upload-area {
  border: 2px dashed #d1d5db;
  border-radius: 16px;
  padding: 3rem 2rem;
  text-align: center;
  transition: all 0.3s ease;
  cursor: pointer;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
  position: relative;
  overflow: hidden;
}

.evidence-upload-area::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(59, 130, 246, 0.02) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.evidence-upload-area.hover::before {
  opacity: 1;
}

.evidence-upload-area.hover {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  transform: translateY(-2px);
  box-shadow: 0 10px 25px -3px rgba(59, 130, 246, 0.1), 0 4px 6px -2px rgba(59, 130, 246, 0.05);
}

.evidence-upload-area.dragover {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  transform: scale(1.02);
  box-shadow: 0 20px 40px -4px rgba(59, 130, 246, 0.2), 0 8px 16px -4px rgba(59, 130, 246, 0.1);
}

.evidence-upload-area.uploading {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  cursor: not-allowed;
}

.evidence-upload-icon {
  margin-bottom: 1.5rem;
  display: flex;
  justify-content: center;
  align-items: center;
}

.evidence-upload-icon-uploading {
  width: 4rem;
  height: 4rem;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  animation: pulse 2s infinite;
}

.evidence-upload-icon-default {
  width: 4rem;
  height: 4rem;
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  transition: all 0.3s ease;
}

.evidence-upload-area.hover .evidence-upload-icon-default {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  transform: scale(1.1);
}

.evidence-upload-icon svg {
  width: 2rem;
  height: 2rem;
}

.evidence-upload-text {
  margin-bottom: 1rem;
}

.evidence-upload-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #374151;
  margin: 0 0 0.5rem 0;
  transition: color 0.3s ease;
}

.evidence-upload-title.uploading {
  color: #1d4ed8;
}

.evidence-upload-title.dragover {
  color: #3b82f6;
}

.evidence-upload-area.hover .evidence-upload-title {
  color: #3b82f6;
}

.evidence-upload-description {
  margin-bottom: 1rem;
}

.evidence-upload-subtitle {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
  transition: color 0.3s ease;
}

.evidence-upload-subtitle.uploading {
  color: #1d4ed8;
}

.evidence-upload-area.hover .evidence-upload-subtitle {
  color: #3b82f6;
}

.evidence-upload-note {
  margin-bottom: 1.5rem;
}

.evidence-upload-note p {
  font-size: 0.75rem;
  color: #9ca3af;
  margin: 0;
}

.evidence-upload-progress {
  margin-bottom: 1.5rem;
}

.evidence-upload-progress-bar {
  width: 100%;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.evidence-upload-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.evidence-upload-progress-text {
  font-size: 0.75rem;
  font-weight: 600;
  color: #1d4ed8;
  margin: 0;
}

.evidence-upload-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.evidence-upload-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  cursor: pointer;
  text-decoration: none;
}

.evidence-upload-btn-primary {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border-color: #3b82f6;
}

.evidence-upload-btn-primary:hover {
  background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.evidence-upload-btn-secondary {
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  color: #374151;
  border-color: #d1d5db;
}

.evidence-upload-btn-secondary:hover {
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #9ca3af;
}

.evidence-upload-btn-icon {
  width: 1rem;
  height: 1rem;
}

/* Responsive Design for Upload Area */
@media (max-width: 768px) {
  .evidence-upload-area {
    padding: 2rem 1rem;
  }
  
  .evidence-upload-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .evidence-upload-btn {
    width: 100%;
    max-width: 200px;
    justify-content: center;
  }
}

.file-item-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.file-item-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* Evidence Attachment Styles */
.evidence-attachment-container {
  background: transparent;
  border-radius: 0;
  box-shadow: none;
  border: none;
  overflow: visible;
}

.attachment-section {
  padding: 0;
  background: transparent;
}

.section-header {
  background: transparent;
  padding: 0;
}

.evidence-section-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 24px 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.evidence-section-title::before {
  display: none;
}

.upload-button-container {
  display: flex;
  justify-content: center;
  padding: 40px 20px;
}

.attach-evidence-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.attach-evidence-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
}

.attach-evidence-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.attach-evidence-icon {
  width: 20px;
  height: 20px;
}

/* Evidence Options */
.evidence-options {
  padding: 32px;
  text-align: center;
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.4s ease;
}

.evidence-options.show {
  opacity: 1;
  transform: translateY(0);
}

.options-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 24px 0;
}

.options-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.option-card {
  background: #ffffff;
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.option-card:hover {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.15);
}

.option-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-radius: 16px;
  margin: 0 auto 16px;
  transition: all 0.3s ease;
}

.option-card:hover .option-icon {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
}

.option-icon svg {
  width: 28px;
  height: 28px;
  color: #3b82f6;
  transition: color 0.3s ease;
}

.option-card:hover .option-icon svg {
  color: #ffffff;
}

.option-card h4 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.option-card p {
  font-size: 0.9rem;
  color: #6b7280;
  margin: 0;
  line-height: 1.5;
}

/* Back Button */
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: #ffffff;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  color: #374151;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
}

.back-btn:hover {
  background: #f9fafb;
  border-color: #d1d5db;
  transform: translateY(-2px);
}

.back-btn.small {
  padding: 8px 16px;
  font-size: 0.85rem;
}

.back-btn-icon {
  width: 16px;
  height: 16px;
}

/* Upload Section */
.file-upload-section {
  padding: 24px;
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.4s ease;
}

.file-upload-section.show {
  opacity: 1;
  transform: translateY(0);
}

.upload-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e5e7eb;
}

.upload-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.select-files-btn {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 14px 28px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #ffffff;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  margin-bottom: 20px;
}

.select-files-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
}

.select-files-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.select-files-icon {
  width: 18px;
  height: 18px;
}

.file-info {
  background: #f8fafc;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
  border-left: 4px solid #3b82f6;
}

.supported-formats {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: #374151;
  margin: 0 0 8px 0;
  font-weight: 500;
}

.info-icon {
  width: 16px;
  height: 16px;
  color: #3b82f6;
}

.max-size {
  font-size: 0.85rem;
  color: #6b7280;
  margin: 0;
}

/* Selected Files */
.selected-files {
  background: #f8fafc;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  opacity: 0;
  transform: translateY(10px);
  transition: all 0.3s ease;
}

.selected-files.show {
  opacity: 1;
  transform: translateY(0);
}

.selected-files h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 16px 0;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px 16px;
  transition: all 0.3s ease;
}

.file-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.file-info-item {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.file-icon {
  width: 20px;
  height: 20px;
  color: #6b7280;
}

.file-name {
  font-size: 0.9rem;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 2px;
}

.file-size {
  font-size: 0.8rem;
  color: #6b7280;
}

.remove-file-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  cursor: pointer;
  transition: all 0.3s ease;
}

.remove-file-btn:hover {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #b91c1c;
}

.remove-icon {
  width: 14px;
  height: 14px;
}

/* Upload Actions */
.upload-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
  border: none;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-2px);
}

.upload-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.clear-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: #ffffff;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  color: #374151;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.clear-btn:hover:not(:disabled) {
  background: #f9fafb;
  border-color: #d1d5db;
  transform: translateY(-2px);
}

.clear-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.upload-icon,
.clear-icon {
  width: 16px;
  height: 16px;
}

/* Upload Progress */
.upload-progress {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  opacity: 0;
  transform: translateY(10px);
  transition: all 0.3s ease;
}

.upload-progress.show {
  opacity: 1;
  transform: translateY(0);
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0f2fe;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #0ea5e9 0%, #0284c7 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.upload-progress p {
  font-size: 0.9rem;
  font-weight: 600;
  color: #0369a1;
  margin: 0;
}

/* Success Message */
.success-message {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 12px;
  padding: 16px 20px;
  text-align: center;
  color: #166534;
  font-size: 0.9rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  opacity: 0;
  transform: translateY(10px);
  transition: all 0.3s ease;
}

.success-message.show {
  opacity: 1;
  transform: translateY(0);
}

.success-icon {
  width: 18px;
  height: 18px;
  color: #16a34a;
}

/* Error Message */
.error-message {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 12px;
  padding: 16px 20px;
  color: #dc2626;
  font-size: 0.9rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  opacity: 0;
  transform: translateY(10px);
  transition: all 0.3s ease;
}

.error-message.show {
  opacity: 1;
  transform: translateY(0);
}

.error-icon {
  width: 18px;
  height: 18px;
  color: #dc2626;
  flex-shrink: 0;
}

/* Link Evidence Section */
.link-evidence-section {
  padding: 24px;
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.4s ease;
  width: 100%;
  max-width: 100%;
}

.link-evidence-section.show {
  opacity: 1;
  transform: translateY(0);
}

.link-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e5e7eb;
}

.link-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.search-container {
  /* Removed background styling */
  margin-bottom: 20px;
  width: 100%;
  max-width: 100%;
}

.search-input-container {
  position: relative;
  margin-bottom: 16px;
}

.search-icon {
  /* Hidden search icon */
  display: none;
}

.search-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  background: #ffffff;
  font-size: 0.9rem;
  color: #374151;
  transition: all 0.3s ease;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-filters {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filter-btn {
  padding: 8px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 20px;
  background: #ffffff;
  color: #6b7280;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.filter-btn:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.filter-btn.active {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-color: #3b82f6;
  color: #ffffff;
}

.search-results {
  min-height: 200px;
  max-height: 70vh;
  overflow-y: auto;
  overflow-x: hidden;
  width: 100%;
  box-sizing: border-box;
}

/* Loading, Error, No Results States */
.loading-state,
.error-state,
.no-results-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.loading-icon,
.error-icon,
.no-results-icon {
  width: 48px;
  height: 48px;
  color: #6b7280;
  margin-bottom: 16px;
}

.loading-state p,
.error-state p,
.no-results-state p {
  font-size: 0.9rem;
  color: #6b7280;
  margin: 0;
}

.retry-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 8px 16px;
  background: #3b82f6;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.retry-btn:hover {
  background: #2563eb;
}

.retry-icon {
  width: 14px;
  height: 14px;
}

/* Events List */
.events-list {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.events-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: #f8fafc;
  border-bottom: 1px solid #e5e7eb;
}

.events-header h4 {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.link-selected-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.link-selected-btn:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  transform: translateY(-1px);
}

.link-icon {
  width: 14px;
  height: 14px;
}

.event-items {
  max-height: 60vh;
  min-height: 200px;
  overflow-y: auto;
  overflow-x: hidden;
  width: 100%;
  box-sizing: border-box;
}

.event-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid #f3f4f6;
  cursor: pointer;
  transition: all 0.3s ease;
}

.event-item:hover {
  background: #f8fafc;
}

.event-item.selected {
  background: #eff6ff;
  border-left: 4px solid #3b82f6;
}

.event-checkbox {
  margin-top: 2px;
}

.event-checkbox input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #3b82f6;
}

.event-content {
  flex: 1;
  min-width: 0;
}

.event-header-info {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.event-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  line-height: 1.4;
}

.event-source {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  flex-shrink: 0;
}

.jira-source {
  background: #dbeafe;
  color: #1e40af;
}

.document-source {
  background: #f3e8ff;
  color: #7c3aed;
}

.riskavaire-source {
  background: #dcfce7;
  color: #166534;
}

.event-details {
  margin-top: 8px;
}

.event-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  color: #6b7280;
  margin-bottom: 8px;
}

.event-framework {
  font-weight: 500;
}

.event-separator {
  color: #d1d5db;
}

.event-timestamp {
  font-weight: 400;
}

.event-description {
  font-size: 0.85rem;
  color: #4b5563;
  margin: 0 0 8px 0;
  line-height: 1.4;
}

.event-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-badge,
.priority-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-new {
  background: #dbeafe;
  color: #1e40af;
}

.status-in-progress {
  background: #fef3c7;
  color: #d97706;
}

.status-completed {
  background: #dcfce7;
  color: #166534;
}

.priority-high {
  background: #fee2e2;
  color: #dc2626;
}

.priority-medium {
  background: #fef3c7;
  color: #d97706;
}

.priority-low {
  background: #f0fdf4;
  color: #16a34a;
}

/* Responsive Design */
@media (max-width: 768px) {
  .options-container {
    grid-template-columns: 1fr;
  }
  
  .upload-header,
  .link-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .upload-actions {
    flex-direction: column;
  }
  
  .search-filters {
    justify-content: center;
  }
  
  .events-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .event-header-info {
    flex-direction: column;
    gap: 8px;
  }
  
  .event-source {
    align-self: flex-start;
  }
}

/* Animations */
@keyframes evidence-fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.evidence-options,
.file-upload-section,
.link-evidence-section {
  animation: evidence-fadeIn 0.4s ease-out;
}

/* Scrollbar Styling for Event Items */
.event-items::-webkit-scrollbar {
  width: 8px;
}

.event-items::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.event-items::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.event-items::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Create Event Type Modal Styles */
.create-event-type-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.create-event-type-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.create-event-type-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.create-event-type-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.create-event-type-close-btn {
  background: none;
  border: none;
  padding: 8px;
  border-radius: 6px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.create-event-type-close-btn:hover {
  background: #e5e7eb;
  color: #374151;
}

.create-event-type-close-icon {
  width: 20px;
  height: 20px;
}

.create-event-type-content {
  padding: 24px;
  flex: 1;
  overflow-y: auto;
}

.create-event-type-form-group {
  margin-bottom: 20px;
}

.create-event-type-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 6px;
}

.create-event-type-required {
  color: #dc2626;
  margin-left: 2px;
}

.create-event-type-char-count {
  color: #6b7280;
  font-size: 0.75rem;
  font-weight: 400;
  margin-left: 8px;
  float: right;
}

.create-event-type-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  transition: all 0.2s;
  background: white;
}

.create-event-type-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.create-event-type-input-disabled {
  background: #f9fafb;
  color: #6b7280;
  cursor: not-allowed;
}

.create-event-type-input-error {
  border-color: #dc2626;
}

.create-event-type-input-error:focus {
  border-color: #dc2626;
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1);
}

.create-event-type-error {
  color: #dc2626;
  font-size: 0.75rem;
  margin-top: 4px;
}

.create-event-type-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

.create-event-type-cancel-btn {
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  color: #374151;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.create-event-type-cancel-btn:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

.create-event-type-create-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: #3b82f6;
  color: white;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.create-event-type-create-btn:hover:not(:disabled) {
  background: #2563eb;
}

.create-event-type-create-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

/* Responsive Design */
@media (max-width: 640px) {
  .create-event-type-overlay {
    padding: 10px;
  }
  
  .create-event-type-container {
    max-height: 95vh;
  }
  
  .create-event-type-header {
    padding: 16px 20px;
  }
  
  .create-event-type-content {
    padding: 20px;
  }
  
  .create-event-type-footer {
    padding: 16px 20px;
    flex-direction: column-reverse;
  }
  
  .create-event-type-cancel-btn,
  .create-event-type-create-btn {
    width: 100%;
    justify-content: center;
  }
}

/* Event Summary Styles */
.event-summary-container {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
  overflow: hidden;
  margin-bottom: 32px;
}

.event-summary-header {
  padding: 24px;
  color: #1f2937;
}

.event-summary-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: #1f2937;
}

.event-summary-subtitle {
  font-size: 0.875rem;
  margin: 0;
  color: #6b7280;
}

.event-summary-content {
  padding: 32px;
}

.event-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

.event-summary-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.event-summary-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0;
}

.event-summary-value {
  font-size: 1rem;
  font-weight: 500;
  color: #1f2937;
  padding: 12px 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  min-height: 44px;
  display: flex;
  align-items: center;
}

.event-summary-description {
  margin-bottom: 24px;
}

.event-summary-description .event-summary-label {
  margin-bottom: 12px;
}

.event-summary-description .event-summary-value {
  min-height: 80px;
  align-items: flex-start;
  padding-top: 16px;
}

.event-summary-additional-records {
  margin-bottom: 24px;
}

.event-summary-additional-records .event-summary-label {
  margin-bottom: 12px;
}

.event-summary-template-yes {
  color: #059669;
  font-weight: 600;
}

.event-summary-template-no {
  color: #6b7280;
  font-weight: 500;
}

/* Responsive Design */
@media (max-width: 768px) {
  .event-summary-content {
    padding: 20px;
  }
  
  .event-summary-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .event-summary-header {
    padding: 20px;
  }
  
  .event-summary-title {
    font-size: 1.25rem;
  }
}
</style>
