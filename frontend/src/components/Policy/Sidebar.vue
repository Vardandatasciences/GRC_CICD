<template>
  <div :class="['sidebar', { collapsed: isCollapsed }]">
    <div class="sidebar-header">
      <div class="logo-container">
        <div class="logo-wrapper" @click="navigate('/home')">
          <img :src="logo" alt="RiskaVaire Logo" class="logo-image" />
        </div>
        <button v-if="!isCollapsed" class="toggle" @click="toggleCollapse">
          {{ isCollapsed ? '»' : '«' }}
        </button>
      </div>
    </div>

    <!-- Expand button for collapsed view -->
    <div v-if="isCollapsed" class="expand-button-container">
      <button class="expand-button" @click="toggleCollapse" title="Expand Sidebar">
        <i class="fas fa-chevron-right"></i>
      </button>
    </div>

    <nav class="menu">
      <!-- Policy Section -->
      <div @click="toggleSubmenu('policy')" class="menu-item has-submenu" :class="{'expanded': openMenus.policy}">
        <i class="fas fa-file-alt icon"></i>
        <span v-if="!isCollapsed">Policy</span>
        <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.policy" class="submenu">
        <!-- 1. Policy Creation -->
        <div @click="toggleSubmenu('policyCreation')" class="menu-item has-submenu" :class="{'expanded': openMenus.policyCreation}">
          <i class="fas fa-plus-square icon"></i>
          <span>Policy Creation</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.policyCreation" class="submenu">
          <div class="menu-item" @click="navigate('/create-policy/create')" :class="{'active': isActive('/create-policy/create')}">
            <i class="fas fa-plus icon"></i>
            <span>Create New Policy</span>
          </div>
          <!-- <div class="menu-item" @click="navigate('/create-policy/framework')">
            <i class="fas fa-sitemap icon"></i>
            <span>Create Framework</span>
          </div> -->
          <div class="menu-item" @click="navigate('/create-policy/upload-framework')" :class="{'active': isActive('/create-policy/upload-framework')}">
            <i class="fas fa-upload icon"></i>
            <span>AI Policy Creation</span>
          </div>
          <div class="menu-item" @click="navigate('/create-policy/tailoring')" :class="{'active': isActive('/create-policy/tailoring')}">
            <i class="fas fa-edit icon"></i>
            <span>Tailoring & Templating</span>
          </div>
          <div class="menu-item" @click="navigate('/create-policy/versioning')" :class="{'active': isActive('/create-policy/versioning')}">
            <i class="fas fa-code-branch icon"></i>
            <span>Versioning</span>
          </div>
        </div>

        <!-- 2. Policies List -->
        <!-- <div class="menu-item" @click="navigate('/policies-list/all')" :class="{'active': isActive('/policies-list/all')}">
          <i class="fas fa-list-alt icon"></i>
          <span>All Policies</span>
        </div> -->

        <div @click="navigate('/framework-explorer')" class="menu-item" :class="{'active': isActive('/framework-explorer')}">
            <i class="fas fa-cubes icon"></i>
            <span>Framework Explorer</span>
          </div>
        

        <!-- 3. Policy Approval -->
        <div class="menu-item" @click="navigate('/policy/approval')" :class="{'active': isActive('/policy/approval')}">
          <i class="fas fa-check-circle icon"></i>
          <span>Policy Approval</span>
        </div>
        <div class="menu-item" @click="navigate('/framework-approval')" :class="{'active': isActive('/framework-approval')}">
          <i class="fas fa-check-circle icon"></i>
          <span>Framework Approval</span>
        </div>
        <div class="menu-item" @click="navigate('/framework-status-changes')" :class="{'active': isActive('/framework-status-changes')}">
          <i class="fas fa-exchange-alt icon"></i>
          <span>Status Change Requests</span>
        </div>

        <!-- 4. Performance Analysis -->
        <div @click="toggleSubmenu('performanceAnalysis')" class="menu-item has-submenu" :class="{'expanded': openMenus.performanceAnalysis}">
          <i class="fas fa-chart-line icon"></i>
          <span>Performance Analysis</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.performanceAnalysis" class="submenu">
          <div class="menu-item" @click="navigate('/policy/performance/kpis')" :class="{'active': isActive('/policy/performance/kpis')}">
            <i class="fas fa-chart-bar icon"></i>
            <span>KPIs Analysis</span>
          </div>
          <div class="menu-item" @click="navigate('/policy/performance/dashboard')" :class="{'active': isActive('/policy/performance/dashboard')}">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>User Dashboard</span>
          </div>
        </div>
      </div>

      
      
<!-- Compliance Section -->
      <div @click="toggleSubmenu('compliances')" class="menu-item has-submenu" :class="{'expanded': openMenus.compliances}">
        <i class="fas fa-check-circle icon"></i>
        <span v-if="!isCollapsed">Compliance</span>
        <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.compliances" class="submenu">
        <!-- 1. Compliance List -->
        <div @click="toggleSubmenu('complianceList')" class="menu-item has-submenu" :class="{'expanded': openMenus.complianceList}">
          <i class="fas fa-list icon"></i>
          <span>Compliance List</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.complianceList" class="submenu">
          <div class="menu-item" @click="navigate('/compliance/list')" :class="{'active': isActive('/compliance/list')}">
            <i class="fas fa-shield-alt icon"></i>
            <span>Control Management</span>
          </div>
          <!-- <div class="menu-item" @click="navigate('/compliance/audit-status/all')" :class="{'active': isActive('/compliance/audit-status/all')}">
            <i class="fas fa-tasks icon"></i>
            <span>Compliance Audit Management</span>
          </div> -->
            <div class="menu-item" @click="navigate('/compliance/audit-management')" :class="{'active': isActive('/compliance/audit-management')}">
              <i class="fas fa-clipboard-check icon"></i>
              <span>Compliance Audit Management</span>
            </div>
          <div class="menu-item" @click="navigate('/compliance/approver')" :class="{'active': isActive('/compliance/approver')}">
            <i class="fas fa-check-double icon"></i>
            <span>Compliance Approval</span>
          </div>
        </div>

        <!-- 2. Compliance Creation -->
        <div @click="toggleSubmenu('complianceCreation')" class="menu-item has-submenu" :class="{'expanded': openMenus.complianceCreation}">
          <i class="fas fa-plus-square icon"></i>
          <span>Compliance Creation</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.complianceCreation" class="submenu">
          <div class="menu-item" @click="navigate('/compliance/create')" :class="{'active': isActive('/compliance/create')}">
            <i class="fas fa-plus icon"></i>
            <span>Create Compliance</span>
          </div>
          <div class="menu-item" @click="navigate('/compliance/tailoring')" :class="{'active': isActive('/compliance/tailoring')}">
            <i class="fas fa-edit icon"></i>
            <span>Tailoring & Templating</span>
          </div>
          <div class="menu-item" @click="navigate('/compliance/versioning')" :class="{'active': isActive('/compliance/versioning')}">
            <i class="fas fa-code-branch icon"></i>
            <span>Versioning</span>
          </div>
        </div>

        <!-- 3. Performance Analysis -->
        <div @click="toggleSubmenu('compliancePerformance')" class="menu-item has-submenu" :class="{'expanded': openMenus.compliancePerformance}">
          <i class="fas fa-chart-line icon"></i>
          <span>Performance Analysis</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.compliancePerformance" class="submenu">
          <div class="menu-item" @click="navigate('/compliance/user-dashboard')" :class="{'active': isActive('/compliance/user-dashboard')}">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>Compliance Dashboard</span>
          </div>
          <div class="menu-item" @click="navigate('/compliance/kpi-dashboard')" :class="{'active': isActive('/compliance/kpi-dashboard')}">
            <i class="fas fa-chart-bar icon"></i>
            <span>Compliance KPI</span>
          </div>
        </div>
      </div>

      <!-- Auditor Section -->
      <div @click="toggleSubmenu('auditor')" class="menu-item has-submenu" :class="{'expanded': openMenus.auditor}">
        <i class="fas fa-user-tie icon"></i>
        <span v-if="!isCollapsed">Auditor</span>
        <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.auditor" class="submenu">
        <div class="menu-item" @click="navigate('/auditor/dashboard')" :class="{'active': isActive('/auditor/dashboard')}">
          <i class="fas fa-th-large icon"></i>
          <span>Audits</span>
        </div>
        <div class="menu-item" @click="navigate('/auditor/assign')" :class="{'active': isActive('/auditor/assign')}">
          <i class="fas fa-check-square icon"></i>
          <span>Assign Audit</span>
        </div>
        <div class="menu-item" @click="navigate('/auditor/ai-audit/2075/upload')" :class="{'active': isActive('/auditor/ai-audit')}">
          <i class="fas fa-robot icon"></i>
          <span>AI Audit Upload</span>
        </div>
        <div class="menu-item" @click="navigate('/auditor/reviews')" :class="{'active': isActive('/auditor/reviews')}">
          <i class="fas fa-tasks icon"></i>
          <span>Review Audits</span>
        </div>
        <div class="menu-item" @click="navigate('/auditor/reports')" :class="{'active': isActive('/auditor/reports')}">
          <i class="fas fa-file-alt icon"></i>
          <span>Audit Reports</span>
        </div>
        <div @click="toggleSubmenu('performance')" class="menu-item has-submenu" :class="{'expanded': openMenus.performance}">
          <i class="fas fa-chart-bar icon"></i>
          <span>Performance Analysis</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="openMenus.performance" class="submenu">
          <div class="menu-item" @click="navigate('/auditor/performance/kpi')" :class="{'active': isActive('/auditor/performance/kpi')}">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>KPIs Analysis</span>
          </div>
          <div class="menu-item" @click="navigate('/auditor/performance/userdashboard')" :class="{'active': isActive('/auditor/performance/userdashboard')}">
            <i class="fas fa-chart-line icon"></i>
            <span>Dashboard</span>
          </div>
        </div>
      </div>
      <!-- Incident Section -->
      <div @click="toggleSubmenu('incident')" class="menu-item has-submenu" :class="{'expanded': openMenus.incident}">
        <i class="fas fa-exclamation-circle icon"></i>
        <span v-if="!isCollapsed">Incident</span>
        <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.incident" class="submenu">
        <div @click="toggleSubmenu('incidentManagement')" class="menu-item has-submenu" :class="{'expanded': openMenus.incidentManagement}">
          <i class="fas fa-clipboard-list icon"></i>
          <span>Incident Management</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.incidentManagement" class="submenu">
          <div class="menu-item" @click="navigate('/incident/incident')" :class="{'active': isActive('/incident/incident')}">
            <i class="fas fa-list icon"></i>
            <span>Incident List</span>
          </div>
          <div class="menu-item" @click="navigate('/incident/create')" :class="{'active': isActive('/incident/create')}">
            <i class="fas fa-plus icon"></i>
            <span>Create Incident</span>
          </div>
          <!-- Audit Findings List -->
          <div class="menu-item" @click="navigate('/incident/audit-findings')" :class="{'active': isActive('/incident/audit-findings')}">
            <i class="fas fa-search icon"></i>
            <span>Audit Findings</span>
          </div>
          <!-- User Tasks -->
          <div class="menu-item" @click="navigate('/incident/user-tasks')" :class="{'active': isActive('/incident/user-tasks')}">
            <i class="fas fa-user-check icon"></i>
            <span>Incident Handling</span>
          </div>
          <!-- AI Import -->
          <div class="menu-item" @click="navigate('/incident/ai-import')" :class="{'active': isActive('/incident/ai-import')}">
            <i class="fas fa-robot icon"></i>
            <span>Incident AI Import</span>
          </div>
        </div>
        <div @click="toggleSubmenu('incidentPerformance')" class="menu-item has-submenu" :class="{'expanded': openMenus.incidentPerformance}">
          <i class="fas fa-chart-line icon"></i>
          <span>Performance Analysis</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.incidentPerformance" class="submenu">
          <div class="menu-item" @click="navigate('/incident/dashboard')" :class="{'active': isActive('/incident/dashboard')}">
            <i class="fas fa-chart-pie icon"></i>
            <span>KPIs Analysis</span>
          </div>
          <div class="menu-item" @click="navigate('/incident/performance/dashboard')" :class="{'active': isActive('/incident/performance/dashboard')}">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>Dashboard</span>
          </div>
        </div>
      </div>
      <!-- Risk Section -->
      <div @click="toggleSubmenu('risk')" class="menu-item has-submenu" :class="{'expanded': openMenus.risk}">
        <i class="fas fa-exclamation-triangle icon"></i>
        <span v-if="!isCollapsed">Risk</span>
        <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.risk" class="submenu">
        
        
        <!-- Risk Register with nested submenu -->
        <div @click="toggleSubmenu('riskRegister')" class="menu-item has-submenu" :class="{'expanded': openMenus.riskRegister}">
          <i class="fas fa-clipboard-list icon"></i>
          <span>Risk Register</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="openMenus.riskRegister" class="submenu nested-submenu">
          <div class="menu-item" @click="navigate('/risk/riskregister-list')" :class="{'active': isActive('/risk/riskregister-list')}">
            <i class="fas fa-list icon"></i>
            <span>Risk Register List</span>
          </div>
          <div class="menu-item" @click="navigate('/risk/create-risk')" :class="{'active': isActive('/risk/create-risk')}">
            <i class="fas fa-plus icon"></i>
            <span>Create Risk</span>
          </div>
          <div class="menu-item" @click="navigate('/risk/ai-document-upload')" :class="{'active': isActive('/risk/ai-document-upload')}">
            <i class="fas fa-file-upload icon"></i>
          <span>Risk Register AI</span>
        </div>
        </div>
        
        <!-- Risk Instances with nested submenu -->
        <div @click="toggleSubmenu('riskInstances')" class="menu-item has-submenu" :class="{'expanded': openMenus.riskInstances}">
          <i class="fas fa-th-list icon"></i>
          <span>Risk Instances</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="openMenus.riskInstances" class="submenu nested-submenu">
          <div class="menu-item" @click="navigate('/risk/riskinstances-list')" :class="{'active': isActive('/risk/riskinstances-list')}">
            <i class="fas fa-list icon"></i>
            <span>Risk Incidents</span>
          </div>
          <div class="menu-item" @click="navigate('/risk/create-instance')" :class="{'active': isActive('/risk/create-instance')}">
            <i class="fas fa-plus icon"></i>
            <span>Create Risk Incident</span>
          </div>
          <div class="menu-item" @click="navigate('/risk/ai-instance-upload')" :class="{'active': isActive('/risk/ai-instance-upload')}">
            <i class="fas fa-robot icon"></i>
            <span>Risk Instance AI</span>
          </div>
          <div class="menu-item" @click="navigate('/risk/scoring')" :class="{'active': isActive('/risk/scoring')}">
            <i class="fas fa-chart-line icon"></i>
            <span>Risk Scoring</span>
          </div>
        </div>
        
        <!-- Risk Handling section -->
        <div @click="navigate('/risk/resolution')" class="menu-item" :class="{'active': isActive('/risk/resolution')}">
          <i class="fas fa-cogs icon"></i>
          <span>Risk Handling</span>
        </div>

        <!-- Risk AI Document Upload -->
        

        <!-- Risk Analytics with collapsible submenu -->
        <div @click="toggleSubmenu('riskAnalytics')" class="menu-item has-submenu" :class="{'expanded': openMenus.riskAnalytics}">
          <i class="fas fa-chart-bar icon"></i>
          <span>Risk Analytics</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="openMenus.riskAnalytics" class="submenu nested-submenu">
          <div class="menu-item" @click="navigate('/risk/riskdashboard')" :class="{'active': isActive('/risk/riskdashboard')}">
            <i class="fas fa-th-large icon"></i>
            <span>Dashboard</span>
          </div>
          <div class="menu-item" @click="navigate('/risk/riskkpi')" :class="{'active': isActive('/risk/riskkpi')}">
            <i class="fas fa-chart-pie icon"></i>
            <span>KPI Dashboard</span>
          </div>
          <!-- Basel KPIs - Only show when Basel III framework is selected -->
          <div v-if="isBaselFramework" class="menu-item" @click="navigate('/risk/baselkpis')" :class="{'active': isActive('/risk/baselkpis')}">
            <i class="fas fa-university icon"></i>
            <span>Basel KPIs</span>
          </div>
        </div>
      </div>

      <!-- Integration Section -->
      <div @click="toggleSubmenu('integration')" class="menu-item has-submenu" :class="{'expanded': openMenus.integration}">
        <i class="fas fa-plug icon"></i>
        <span v-if="!isCollapsed">Integration</span>
        <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.integration" class="submenu">
        <div class="menu-item" @click="navigate('/integration/external')" :class="{'active': isActive('/integration/external')}">
          <i class="fas fa-external-link-alt icon"></i>
          <span>External Integrations</span>
        </div>
        <div class="menu-item" @click="navigate('/integration/streamline')" :class="{'active': isActive('/integration/streamline')}">
          <i class="fas fa-stream icon"></i>
          <span>Streamline</span>
        </div>
      </div>

      <!-- Document Handling Section -->
      <div @click="navigate('/document-handling')" class="menu-item" :class="{'active': isActive('/document-handling')}">
        <i class="fas fa-folder-open icon"></i>
        <span v-if="!isCollapsed" class="bold-text">Document Handling</span>
      </div>

      <!-- Data Workflow Section -->
      <div @click="navigate('/data-workflow')" class="menu-item" :class="{'active': isActive('/data-workflow')}">
        <i class="fas fa-project-diagram icon"></i>
        <span v-if="!isCollapsed" class="bold-text">Data Workflow</span>
      </div>
      <!-- KPI Dashboard Section -->
      <div @click="navigate('/kpis')" class="menu-item" :class="{'active': isActive('/kpis')}">
        <i class="fas fa-chart-line icon"></i>
        <span v-if="!isCollapsed" class="bold-text">{{ kpiLabel }}</span>
      </div>

            <!-- Migration Gap Analysis Section -->
            <div @click="toggleSubmenu('frameworkMigration')" class="menu-item has-submenu" :class="{'expanded': openMenus.frameworkMigration}">
        <i class="fas fa-exchange-alt icon"></i>
        <span v-if="!isCollapsed">Change Management</span>
        <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.frameworkMigration" class="submenu">
        <div class="menu-item" @click="navigate('/framework-migration')" :class="{'active': isActive('/framework-migration')}">
          <i class="fas fa-tachometer-alt icon"></i>
          <span>Overview</span>
        </div>
        <div class="menu-item" @click="navigate('/framework-migration/comparison')" :class="{'active': isActive('/framework-migration/comparison')}">
          <i class="fas fa-balance-scale icon"></i>
          <span>Framework Comparison</span>
        </div>
        <div class="menu-item" @click="navigate('/framework-migration/migration')" :class="{'active': isActive('/framework-migration/migration')}">
          <i class="fas fa-route icon"></i>
          <span>Gap Analysis</span>
        </div>
      </div>
      <!-- Event Handling Section -->
       <div @click="toggleSubmenu('eventHandling')" class="menu-item has-submenu" :class="{'expanded': openMenus.eventHandling}">
         <i class="fas fa-calendar-alt icon"></i>
         <span v-if="!isCollapsed">Event Handling</span>
         <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
       </div>
       <div v-if="!isCollapsed && openMenus.eventHandling" class="submenu">
         <!-- Event Management -->
         <div @click="toggleSubmenu('eventManagement')" class="menu-item has-submenu" :class="{'expanded': openMenus.eventManagement}">
           <i class="fas fa-clipboard-list icon"></i>
           <span>Event Management</span>
           <i class="fas fa-chevron-right submenu-arrow"></i>
         </div>
         <div v-if="!isCollapsed && openMenus.eventManagement" class="submenu">
           <div class="menu-item" @click="navigate('/event-handling/list')" :class="{'active': isActive('/event-handling/list')}">
             <i class="fas fa-list icon"></i>
             <span>Events List</span>
           </div>
           <div class="menu-item" @click="navigate('/event-handling/create')" :class="{'active': isActive('/event-handling/create')}">
             <i class="fas fa-plus icon"></i>
             <span>Create Event</span>
           </div>
           <div class="menu-item" @click="navigate('/event-handling/queue')" :class="{'active': isActive('/event-handling/queue')}">
             <i class="fas fa-clock icon"></i>
             <span>Events Queue</span>
           </div>
           <!-- <div class="menu-item" @click="navigate('/event-handling/evidence-attachment')" :class="{'active': isActive('/event-handling/evidence-attachment')}">
             <i class="fas fa-paperclip icon"></i>
             <span>Evidence Attachment</span>
           </div> -->
         </div>

         <!-- Event Calendar -->
         <div class="menu-item" @click="navigate('/event-handling/calendar')" :class="{'active': isActive('/event-handling/calendar')}">
           <i class="fas fa-calendar icon"></i>
           <span>Calendar</span>
         </div>

         <!-- Event Approval -->
         <div class="menu-item" @click="navigate('/event-handling/approval')" :class="{'active': isActive('/event-handling/approval')}">
           <i class="fas fa-check-circle icon"></i>
           <span>Approval</span>
         </div>

         <!-- Event Archive -->
         <div class="menu-item" @click="navigate('/event-handling/archived')" :class="{'active': isActive('/event-handling/archived')}">
           <i class="fas fa-archive icon"></i>
           <span>Archived</span>
         </div>

         <!-- Event Dashboard -->
         <div class="menu-item" @click="navigate('/event-handling/dashboard')" :class="{'active': isActive('/event-handling/dashboard')}">
           <i class="fas fa-tachometer-alt icon"></i>
           <span>Event Dashboard</span>
         </div>
       </div>
     

    </nav>

    <div class="bottom-section">
      <!-- Notifications Tab -->
      <div @click="navigate('/notifications')" class="notification-menu-item">
        <i class="fas fa-bell icon bell-theme"></i>
        <span v-if="!isCollapsed">Notifications</span>
        <span v-if="unreadCount > 0" class="notification-badge">{{ unreadCount }}</span>
        <audio ref="notifAudio" src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" preload="auto"></audio>
      </div>
      


<!-- Help Section -->
       <div @click="toggleSubmenu('help')" class="help-menu-item">
         <i class="fas fa-question-circle icon help-theme"></i>
         <span v-if="!isCollapsed">Help</span>
         <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
       </div>
       <div v-if="!isCollapsed && openMenus.help" class="help-submenu">
         <div class="help-menu-item" @click="navigate('/help/contact-us')" :class="{'active': isActive('/help/contact-us')}">
           <i class="fas fa-phone-alt icon"></i>
           <span>Contact Us</span>
         </div>
         <div class="help-menu-item" @click="navigate('/help/faqs')" :class="{'active': isActive('/help/faqs')}">
           <i class="fas fa-question icon"></i>
           <span>FAQs (Frequently Asked Questions)</span>
         </div>
         <div class="help-menu-item" @click="navigate('/help/user-manual')" :class="{'active': isActive('/help/user-manual')}">
           <i class="fas fa-book icon"></i>
           <span>User Manual</span>
         </div>
         <div class="help-menu-item" @click="navigate('/help/privacy-security')" :class="{'active': isActive('/help/privacy-security')}">
           <i class="fas fa-shield-alt icon"></i>
           <span>Privacy & Security</span>
         </div>
         <div class="help-menu-item" @click="navigate('/help/help-us-improve')" :class="{'active': isActive('/help/help-us-improve')}">
           <i class="fas fa-lightbulb icon"></i>
           <span>Feedback</span>
         </div>
         <div class="help-menu-item" @click="navigate('/help/acknowledgement')" :class="{'active': isActive('/help/acknowledgement')}">
           <i class="fas fa-handshake icon"></i>
           <span>Acknowledgement</span>
         </div>
       </div>      <!-- User Profile -->
      <div class="bottom-profile" @click="navigate('/user-profile')">
        <i class="fas fa-user icon"></i>
        <span v-if="!isCollapsed">{{ username }}</span>
      </div>
      
      <!-- RBAC Test -->
      <!-- <div class="menu-item" @click="navigate('/rbac-test')" :class="{'active': isActive('/rbac-test')}">
        <i class="fas fa-shield-alt icon"></i>
        <span v-if="!isCollapsed">🔐 RBAC Test</span>
      </div> -->
      
      <!-- Logout Button -->
      <!-- <div class="logout-button" @click="handleLogoutClick">
        <i class="fas fa-sign-out-alt icon"></i>
        <span v-if="!isCollapsed">Logout</span>
      </div> -->
    </div>
  </div>
</template>

<script>
import {  API_ENDPOINTS } from '../../config/api.js'
import axios from 'axios'
import authService from '../../services/authService.js'

import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useStore } from 'vuex'
import logo from '../../assets/RiskaVaire.png'
import '@fortawesome/fontawesome-free/css/all.min.css'
import eventBus, { LOGOUT_EVENT } from '../../utils/eventBus.js'

export default {
  name: 'PolicySidebar',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const store = useStore()
    const isCollapsed = ref(false)
    const themeMenuOpen = ref(false)
    const currentTheme = ref('light')
    const unreadCount = ref(0)
    const username = ref('User')
    let prevUnreadCount = 0
    let pollInterval = null
    const notifAudio = ref(null)
    
    // Compute current route path for active highlighting
    const currentPath = computed(() => route.path)
    const selectedFrameworkName = computed(() => {
      const framework = store.getters['framework/selectedFramework']
      const name = framework?.name?.trim()
      return name && name.toLowerCase() !== 'all frameworks' ? name : 'All Frameworks'
    })
    const kpiLabel = computed(() => {
      return selectedFrameworkName.value === 'All Frameworks'
        ? 'KPIs'
        : `${selectedFrameworkName.value} KPIs`
    })
    
    // Check if Basel III framework is selected
    const isBaselFramework = computed(() => {
      const frameworkName = selectedFrameworkName.value.toLowerCase()
      return frameworkName.includes('basel') && (frameworkName.includes('iii') || frameworkName.includes('3'))
    })
    
    const openMenus = ref({
      policy: false,
      policyCreation: false,
      performanceAnalysis: false,
      frameworkMigration: false,
      integration: false,
      compliance: false,
      risk: false,
      riskRegister: false,
      riskInstances: false,
      riskAnalytics: false,
      auditor: false,
      incident: false,
      incidentManagement: false,
      incidentPerformance: false,
      dashboard: false,
      complianceDashboard: false,
      policyManagement: false,
      createPolicy: false,
      performance: false,
      auditFindings: false,
      compliances: false,
      compliancesView: false,
      complianceCreation: false,
      complianceList: false,
      compliancePerformance: false
    })

    // Check if route is active
    const isActive = (path) => {
      // Exact match
      if (currentPath.value === path) {
        return true
      }
     
      // Special handling for framework migration routes
      // Only match parent route if we're exactly on it, not on child routes
      if (path === '/framework-migration') {
        return currentPath.value === '/framework-migration'
      }
     
      // For other routes, check if current path starts with the given path
      return currentPath.value.startsWith(path + '/')
    }
    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value
    }

    const toggleSubmenu = (section) => {
      openMenus.value[section] = !openMenus.value[section]
    }

    const toggleThemeMenu = () => {
      themeMenuOpen.value = !themeMenuOpen.value
    }

    const setTheme = (theme) => {
      currentTheme.value = theme
      document.documentElement.setAttribute('data-theme', theme)
      localStorage.setItem('selected-theme', theme)
      themeMenuOpen.value = false
    }

    const handleDashboardClick = () => {
      toggleSubmenu('dashboard')
      if (!openMenus.value.dashboard) {
        router.push('/policy/dashboard')
      }
    }

    const navigate = (path) => {
      // Simple navigation without interceptor interference
      router.push(path)
    }

    // Poll unread notifications every 10 seconds
    const fetchUnreadCount = async () => {
      try {
        // Check if user is still authenticated before making the request
        const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true'
        const accessToken = localStorage.getItem('access_token')
        const userId = localStorage.getItem('user_id')
        
        // More comprehensive authentication check
        if (!isAuthenticated || !accessToken || !userId) {
          console.log('User not authenticated - stopping notification polling')
          if (pollInterval) {
            clearInterval(pollInterval)
            pollInterval = null
          }
          return
        }
        
        // Verify token is still valid by checking its expiration
        try {
          const tokenPayload = JSON.parse(atob(accessToken.split('.')[1]))
          const currentTime = Math.floor(Date.now() / 1000)
          
          if (tokenPayload.exp && tokenPayload.exp < currentTime) {
            console.log('Token expired - stopping notification polling')
            if (pollInterval) {
              clearInterval(pollInterval)
              pollInterval = null
            }
            return
          }
        } catch (tokenError) {
          console.log('Invalid token format - stopping notification polling')
          if (pollInterval) {
            clearInterval(pollInterval)
            pollInterval = null
          }
          return
        }
        
        // Use axios with JWT authentication instead of fetch
        const response = await axios.get(API_ENDPOINTS.GET_NOTIFICATIONS(userId), {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          },
          timeout: 5000 // 5 second timeout to prevent hanging requests
        });
        
        if (response.data && response.data.status === 'success') {
          const count = (response.data.notifications || []).filter(n => n.status && !n.status.isRead).length;
          if (count > prevUnreadCount && prevUnreadCount !== 0) {
            // Play sound only if new notification arrives (not on first load)
            if (notifAudio.value) notifAudio.value.play();
          }
          unreadCount.value = count;
          prevUnreadCount = count;
        }
      } catch (e) {
        // Handle different types of errors
        if (e.response) {
          // Server responded with error status
          if (e.response.status === 401) {
            console.log('Unauthorized (401) - stopping notification polling')
            if (pollInterval) {
              clearInterval(pollInterval)
              pollInterval = null
            }
          } else if (e.response.status === 403) {
            console.log('Forbidden (403) - stopping notification polling')
            if (pollInterval) {
              clearInterval(pollInterval)
              pollInterval = null
            }
          } else {
            // Other server errors - log but don't stop polling
            console.log(`Notification fetch server error: ${e.response.status} - ${e.response.statusText}`);
          }
        } else if (e.request) {
          // Network error - don't stop polling for network issues
          console.log('Notification fetch network error - will retry');
        } else {
          // Other errors - don't stop polling
          console.log('Notification fetch error:', e.message);
        }
      }
    }

    // Get logged in username
    const fetchUsername = async () => {
      try {
        // Try all possible sources for the user's name
        const storedFullName = localStorage.getItem('fullName')
        const storedUsername = localStorage.getItem('username')
        const userData = localStorage.getItem('user')
        let fallback = 'User'
        if (userData) {
          try {
            const userObj = JSON.parse(userData)
            fallback = userObj.full_name || userObj.UserName || userObj.user_name || userObj.username || fallback
          } catch (e) {
            console.error('Error parsing user data:', e)
          }
        }
        if (storedFullName && storedFullName !== 'null') {
          username.value = storedFullName
        } else if (storedUsername && storedUsername !== 'null') {
          username.value = storedUsername
        } else {
          username.value = fallback
        }
      } catch (e) {
        console.error('Error fetching username:', e)
        username.value = 'User'
      }
    }

    // Handle logout event
    const handleLogout = () => {
      console.log('🛑 Logout event received - stopping notification polling')
      if (pollInterval) {
        clearInterval(pollInterval)
        pollInterval = null
      }
    }

    // Handle login event - restart notification polling
    const handleLogin = () => {
      console.log('🛡️ Login event received - notification polling already running')
      // Do nothing - polling is already running
    }

    // Handle logout click
    const handleLogoutClick = async () => {
      try {
        console.log('🔄 Logging out...')
        await authService.logout()
        console.log('✅ Logout successful')
        router.push('/login')
      } catch (error) {
        console.error('❌ Logout error:', error)
        // Force redirect to login even if logout fails
        router.push('/login')
      }
    }

    onMounted(() => {
      // COMPLETELY DISABLED: Always start notification polling to prevent logout issues
      console.log('🛡️ Sidebar authentication check disabled - always authenticated')
      fetchUnreadCount();
      pollInterval = setInterval(fetchUnreadCount, 600000);
      
      fetchUsername();
      const savedTheme = localStorage.getItem('selected-theme') || 'light'
      setTheme(savedTheme)
      
      // Listen for user data updates
      window.addEventListener('userDataUpdated', fetchUsername)
      
      // Listen for authentication events
      window.addEventListener('authChanged', handleLogin)
      eventBus.on(LOGOUT_EVENT, handleLogout)
    })
    onUnmounted(() => {
      if (pollInterval) clearInterval(pollInterval)
      window.removeEventListener('userDataUpdated', fetchUsername)
      window.removeEventListener('authChanged', handleLogin)
      eventBus.off(LOGOUT_EVENT, handleLogout)
    })

    return {
      isCollapsed,
      openMenus,
      themeMenuOpen,
      currentTheme,
      logo,
      username,
      toggleCollapse,
      toggleSubmenu,
      toggleThemeMenu,
      setTheme,
      navigate,
      handleDashboardClick,
      unreadCount,
      notifAudio,
      isActive,
      handleLogoutClick,
      kpiLabel,
      isBaselFramework
    }
  }
}
</script>

<style scoped>
/* Import the existing CSS file */
@import './sidebar.css';

/* Notification tab style */
.notification-menu-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: background 0.2s;
  position: relative;
}
.notification-menu-item:hover {
  background: #f0f4ff;
}
.notification-menu-item .icon {
  margin-right: 12px;
  font-size: 1.2rem;
  color: #575757 !important;
}
.bell-theme {
  color:  #646464 !important;
}
/* Help menu item style */
.help-menu-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: background 0.2s;
  position: relative;
  font-weight: 600;
}
.help-menu-item:hover {
  background: #f0f4ff;
}
.help-menu-item .icon {
  margin-right: 12px;
  font-size: 1.2rem;
  color: #575757 !important;
}
.help-theme {
  color: #646464 !important;
}
.help-submenu {
  background: #f8f9fa;
  border-left: 3px solid #007bff;
}
.help-submenu .help-menu-item {
  padding: 10px 20px 10px 40px;
  font-weight: 500;
  font-size: 0.9rem;
}
.help-submenu .help-menu-item:hover {
  background: #e3f2fd;
}
.help-submenu .help-menu-item.active {
  background: #007bff;
  color: white !important;
}
.help-submenu .help-menu-item.active .icon {
  color: white !important;
}
.notification-badge {
  position: absolute;
  top: 2px;
  left: 28px;
  background:  #ff3e3e !important;
  color: #fff;
  border-radius: 50%;
  font-size: 0.8rem;
  min-width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  box-shadow: 0 1px 4px rgba(25, 118, 210, 0.18);
  z-index: 2;
}



/* Expand button styles */
.expand-button-container {
  display: flex;
  justify-content: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color, #333);
  flex-shrink: 0;
  background-color: #ffffff;
}

.expand-button {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: var(--hover-bg, #333);
  border: 1px solid var(--border-color, #333);
  color: var(--text-primary, #ffffff);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.expand-button:hover {
  background-color: var(--active-bg, #4a90e2);
  transform: scale(1.1);
}

.expand-button i {
  font-size: 0.9rem;
}

/* Active menu item styles */
.menu-item.active {
  background-color: rgba(0, 51, 153, 0.1);
  color: #003399 !important;
  font-weight: 600;
  border-left: 3px solid #003399;
}

.menu-item.active .icon {
  color: #003399 !important;
}

/* Dark theme active item adjustments */
[data-theme="dark"] .menu-item.active {
  background-color: rgba(64, 115, 255, 0.2);
  color: #4073ff !important;
  border-left: 3px solid #4073ff;
}

[data-theme="dark"] .menu-item.active .icon {
  color: #4073ff !important;
}

/* Blue theme active item adjustments */
[data-theme="blue"] .menu-item.active {
  background-color: rgba(255, 255, 255, 0.15);
  color: #ffffff !important;
  border-left: 3px solid #ffffff;
}

[data-theme="blue"] .menu-item.active .icon {
  color: #ffffff !important;
}

/* Logout button styles */
.logout-button {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: background 0.2s;
  color: #ff4757;
  border-top: 1px solid #e0e0e0;
  margin-top: auto;
}

.logout-button:hover {
  background: #fff5f5;
}

.logout-button .icon {
  margin-right: 12px;
  font-size: 1.2rem;
  color: #ff4757 !important;
}

.logout-button span {
  font-weight: 500;
  color: #ff4757;
}

/* Bold text class */
.bold-text {
  font-weight: bold !important;
}
</style> 