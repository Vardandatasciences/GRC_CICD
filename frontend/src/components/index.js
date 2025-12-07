import { createRouter, createWebHistory } from 'vue-router'
import PolicyDashboard from '../components/Policy/PolicyDashboard.vue'
import CreatePolicy from '../components/Policy/CreatePolicy.vue'
import PerformancePage from '../components/Policy/PerformancePage.vue'
import PolicyApprover from '../components/Policy/PolicyApprover.vue'
import AllPolicies from '../components/Policy/AllPolicies.vue'
// import AssignAudit from '../components/Auditor/AssignAudit.vue'
import ActivePolicies from '../components/Policy/ActivePolicies.vue'
import Framework from '../components/Policy/Framework.vue'
import VV from '../components/Policy/VV.vue'
import TreePolicies from '../components/Policy/TreePolicies.vue'
// import CreatePolicy from '../components/Policy/CreatePolicy.vue'
import FrameworkExplorer from '../components/Policy/FrameworkExplorer.vue'
import FrameworkPolicies from '../components/Policy/FrameworkPolicies.vue'
import KPIDashboard from '../components/Policy/KPIDashboard.vue'
import FrameworkApprover from '../components/Framework/FrameworkApprover.vue'
import StatusChangeRequests from '../components/Policy/StatusChangeRequests.vue'
import StatusChangeDetails from '../components/Policy/StatusChangeDetails.vue'
import TT from '../components/Policy/TT.vue'
 
import AssignAudit from '../components/Auditor/AssignAudit.vue'
import AIAuditDocumentUpload from '../components/Auditor/AIAuditDocumentUpload.vue'
import AuditorDashboard from '../components/Auditor/AuditorDashboard.vue'
import Reviewer from '../components/Auditor/Reviewer.vue'
import TaskView from '../components/Auditor/TaskView.vue'
import ReviewTaskView from '../components/Auditor/ReviewTaskView.vue'
import ReviewConfirmation from '../components/Auditor/ReviewConfirmation.vue'
import AuditReport from '../components/Auditor/AuditReport.vue'
import AuditReportView from '../components/Auditor/AuditReportView.vue'
import AuditFindingDetailsView from '../components/Auditor/AuditFindingDetailsView.vue'
import PerformanceAnalysis from '../components/Auditor/PerformanceAnalysis.vue'
import KPIAnalysis from '../components/PerformanceAnalysis/KpiAnalysis.vue'
import PerformanceDashboard from '../components/Auditor/UserDashboard.vue'
import UploadFramework from '../components/Policy/UploadFramework.vue'
 
// import AuditorDashboard from '../components/Auditor/AuditorDashboard.vue'
// import Reviewer from '../components/Auditor/Reviewer.vue'
import CreateIncident from '../components/Incident/CreateIncident.vue'
import IncidentDashboard from '../components/Incident/IncidentDashboard.vue'
import IncidentManagement from '../components/Incident/Incident.vue'
import IncidentDetails from '@/components/Incident/IncidentDetails.vue'
import AuditFindings from '@/components/Incident/AuditFindings.vue'
import AuditFindingDetails from '@/components/Incident/AuditFindingDetails.vue'
 
 
// import UserTasks from '../components/Incident/UserTasks.vue'
import IncidentUserTasks from '../components/Incident/IncidentUserTasks.vue'
// import CreateCompliance from '../components/Compliance/CreateCompliance.vue'
// import CrudCompliance from '../components/Compliance/CrudCompliance.vue'
// import ComplianceVersioning from '../components/Compliance/ComplianceVersioning.vue'
 
import Audits from '../components/Auditor/Audits.vue'
 
// import AllCompliance from '../components/Compliance/AllCompliance.vue'
// import ComplianceDashboard from '../components/Compliance/ComplianceDashboard.vue'
import CreateCompliance from '../components/Compliance/CreateCompliance.vue'
// import ComplianceVersioning from '../components/Compliance/ComplianceVersioning.vue'
// import ComplianceApprover from '../components/Compliance/ComplianceApprover.vue'
// import ComplianceVersionList from '../components/Compliance/ComplianceVersionList.vue'
 
 
 
// EventHandling Components
import EventsDashboard from '../components/EventHandling/EventsDashboard.vue'
import EventsList from '../components/EventHandling/EventsList.vue'
import EventsQueue from '../components/EventHandling/EventsQueue.vue'
import EventsCalendar from '../components/EventHandling/EventsCalendar.vue'
import EventsApproval from '../components/EventHandling/EventsApproval.vue'
import ArchivedEvents from '../components/EventHandling/ArchivedEvents.vue'
import EventCreation from '../components/EventHandling/EventCreation.vue'
import Layout from '../components/EventHandling/Layout.vue'
import EventViewPopup from '../components/EventHandling/EventViewPopup.vue'
import EvidenceAttachment from '../components/EventHandling/EvidenceAttachment.vue'
 
import ApprovalModal from '../components/EventHandling/ApprovalModal.vue'
 
 
import EditCompliance from '../components/Compliance/EditCompliance.vue'
import CopyCompliance from '../components/Compliance/CopyCompliance.vue'
import ComplianceApprover from '../components/Compliance/ComplianceApprover.vue'
import ComplianceDetails from '../components/Compliance/ComplianceDetails.vue'
import AllCompliance from '../components/Compliance/AllCompliance.vue'
import Compliances from '../components/Compliance/Compliances.vue'
import ComplianceView from '../components/Compliance/ComplianceView.vue'
import ComplianceAuditView from '../components/Compliance/ComplianceAuditView.vue'
import ComplianceDashboard from '../components/Compliance/ComplianceDashboard.vue'
import ComplianceTailoring from '../components/Compliance/ComplianceTailoring.vue'
import ComplianceVersioning from '../components/Compliance/ComplianceVersioning.vue'
import ComplianceKPI from '../components/Compliance/ComplianceKPINew.vue'
import PopupDemo from '../components/Compliance/PopupDemo.vue'
import ComplianceDebug from '../components/Compliance/ComplianceDebug.vue'
 
import Notifications from '../views/Notifications.vue'
 
 
 
 
import CreateRisk from '../components/Risk/CreateRisk.vue'
import RiskRegisterList from '../components/Risk/RiskRegisterList.vue'
import RiskDashboard from '../components/Risk/RiskDashboard.vue'
import RiskInstances from '../components/Risk/RiskInstances.vue'
import CreateRiskInstance from '../components/Risk/CreateRiskInstance.vue'
import RiskWorkflow from '../components/Risk/RiskWorkflow.vue'
import TailoringRisk from '../components/Risk/TailoringRisk.vue'
import RiskKPI from '../components/Risk/RiskKPI.vue'
import BaselKPI from '../components/Risk/baselkpi.vue'
import RiskScoring from '../components/Risk/RiskScoring.vue'
import ScoringDetails from '../components/Risk/ScoringDetails.vue'
import RiskResolution from '../components/Risk/RiskResolution.vue'
import ViewRisk from '../components/Risk/ViewRisk.vue'
import ViewInstance from '../components/Risk/ViewInstance.vue'
 
import LoginView from '../components/Login/LoginView.vue'
import HomeView from '../components/Login/HomeView.vue'
import UserProfile from '../components/Login/UserProfile.vue'
import AccessDenied from '../views/AccessDenied.vue'
import RBACTest from '../components/RBACTest.vue'
import TestAccessDenied from '../components/TestAccessDenied.vue'
import DocumentHandling from '../components/DocumentHandling/DocumentHandling.vue'
import DataWorkflowTree from '../components/Tree/tree.vue'
 
import ContactUs from '../components/Help/ContactUs.vue'
import FAQs from '../components/Help/FAQs.vue'
import UserManual from '../components/Help/UserManual.vue'
import PrivacySecurity from '../components/Help/PrivacySecurity.vue'
import HelpUsImprove from '../components/Help/HelpUsImprove.vue'
import Acknowledgement from '../components/Help/Acknowledgement.vue'
 
const routes = [
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/home',
    name: 'home',
    component: HomeView,
    meta: { requiresAuth: true }
  },
  {
    path: '/',
    redirect: '/login',
    meta: { requiresAuth: false }
  },
 
  {
    path: '/policy/dashboard',
    name: 'PolicyDashboard',
    component: PolicyDashboard,
    meta: {
      requiresAuth: true,
      requiresPermission: { module: 'policy', permission: 'view_all_policy' }
    }
  },
  {
    path: '/policy/performance',
    name: 'PerformancePage',
    component: PerformancePage,
    meta: { requiresAuth: true }
  },
  {
    path: '/policy/approver',
    name: 'PolicyApprover',
    component: PolicyApprover,
    meta: {
      requiresAuth: true,
      requiresPermission: { module: 'policy', permission: 'approve_policy' }
    }
  },
  {
    path: '/policies-list/all',
    name: 'AllPolicies',
    component: AllPolicies,
    meta: { requiresAuth: true }
  },
  {
    path: '/policies-list/active',
    name: 'ActivePolicies',
    component: ActivePolicies,
    meta: { requiresAuth: true }
  },
  {
    path: '/create-policy/upload-framework',
    name: 'UploadFramework',
    component: UploadFramework
  },
  {
    path: '/create-policy/create',
    name: 'CreatePolicy',
    component: CreatePolicy,
    meta: {
      requiresAuth: true,
      requiresPermission: { module: 'policy', permission: 'create_policy' }
    }
  },
  {
    path: '/create-policy/framework',
    name: 'Framework',
    component: Framework,
    meta: { requiresAuth: true }
  },
  {
    path: '/create-policy/tailoring',
    name: 'TT',
    component: TT,
    meta: { requiresAuth: true }
  },
  {
    path: '/create-policy/versioning',
    name: 'Versioning',
    component: VV,
    meta: { requiresAuth: true }
  },
  {
    path: '/tree-policies',
    name: 'TreePolicies',
    component: TreePolicies,
    meta: { requiresAuth: true }
  },
  {
    path: '/compliance/create',
    name: 'CreateCompliance',
    component: CreateCompliance
  },
  {
    path: '/incident/user-tasks',
    name: 'IncidentUserTasks',
    component: IncidentUserTasks
  },
  // {
  //   path: '/compliance/versioning',
  //   name: 'ComplianceVersioning',
  //   component: ComplianceVersioning
  // },
  {
    path: '/compliance/approver',
    name: 'ComplianceApprover',
    component: ComplianceApprover
  },
  {
    path: '/compliance/details/:complianceId',
    name: 'ComplianceDetails',
    component: ComplianceDetails,
    meta: { requiresAuth: true }
  },
  {
    path: '/status-change-requests',
    name: 'StatusChangeRequests',
    component: StatusChangeRequests,
    meta: { requiresAuth: true }
  },
  {
    path: '/status-change-details/:requestId',
    name: 'StatusChangeDetails',
    component: StatusChangeDetails,
    meta: { requiresAuth: true }
  },
  // {
  //   path: '/compliance/version-list',
  //   name: 'ComplianceVersionList',
  //   component: ComplianceVersionList
  // },
  // {
  //   path: '/compliance/list',
  //   name: 'AllCompliance',
  //   component: AllCompliance
  // },
 
  {
    path: '/auditor/dashboard',
    name: 'AuditorDashboard',
    component: () => import('../components/Auditor/AuditorDashboard.vue'),
    meta: {
      requiresAuth: true,
      requiresPermission: { module: 'audit', permission: 'view_audit_reports' }
    }
  },
  {
    path: '/auditor/assign',
    name: 'AssignAudit',
    component: AssignAudit,
    meta: {
      requiresAuth: true,
      requiresPermission: { module: 'audit', permission: 'assign_audit' }
    }
  },
  {
    path: '/auditor/ai-audit/:auditId/upload',
    name: 'AIAuditDocumentUpload',
    component: AIAuditDocumentUpload,
    meta: {
      requiresAuth: true,
      requiresPermission: { module: 'audit', permission: 'conduct_audit' }
    }
  },
  {
    path: '/auditor/reviews',
    name: 'ReviewAudits',
    component: Reviewer,
    meta: {
      requiresAuth: true,
      requiresPermission: { module: 'audit', permission: 'review_audit' }
    }
  },
  {
    path: '/auditor/reviewer',
    name: 'AuditorReviewer',
    component: Reviewer,
    meta: {
      requiresAuth: true,
      requiresPermission: { module: 'audit', permission: 'review_audit' }
    }
  },
  {
    path: '/audit/:auditId/tasks',
    name: 'TaskView',
    component: TaskView,
    props: true
  },
  {
    path: '/reviewer/task/:auditId',
    name: 'ReviewTaskView',
    component: ReviewTaskView,
    props: true
  },
  {
    path: '/auditor/audits',
    name: 'Audits',
    component: Audits
  },
  {
    path: '/auditor/kpi',
    name: 'AuditorKPI',
    component: () => import('../components/Auditor/AuditorDashboard.vue')
  },
  {
    path: '/incident/create',
    name: 'CreateIncident',
    component: CreateIncident
  },
  {
    path: '/incident/incident',
    name: 'Incident',
    component: IncidentManagement
  },
  {
    path: '/incident/dashboard',
    name: 'IncidentDashboard',
    component: IncidentDashboard
  },
  {
    path: '/incident/:id',
    name: 'IncidentDetails',
    component: IncidentDetails,
    props: true
  },
  {
    path: '/incident/audit-findings',
    name: 'AuditFindings',
    component: AuditFindings
  },
  {
    path: '/incident/audit-finding-details/:id',
    name: 'AuditFindingDetails',
    component: AuditFindingDetails,
    props: true
  },
  {
    path: '/compliance/approver',
    name: 'ComplianceApprover',
    component: ComplianceApprover
  },
  {
    path: '/incident/incident',
    name: 'IncidentManagement',
    component: () => import('../components/Incident/Incident.vue')
  },
  {
    path: '/incident/performance/dashboard',
    name: 'IncidentPerformanceDashboard',
    component: () => import('../components/Incident/IncidentPerformanceDashboard.vue')
 
 
  },{
    path: '/risk/create',
    name: 'CreateRisk',
    component: CreateRisk
  },
  {
    path: '/risk/riskregister',
    name: 'RiskRegister',
    redirect: '/risk/riskregister-list'
  },
  {
    path: '/risk/riskregister-list',
    name: 'RiskRegisterList',
    component: RiskRegisterList
  },
  {
    path: '/risk/create-risk',
    name: 'CreateRiskForm',
    component: CreateRisk
  },
  {
    path: '/risk/riskdashboard',
    name: 'RiskDashboard',
    component: RiskDashboard
  },
  {
    path: '/risk/riskinstances',
    name: 'RiskInstances',
    redirect: '/risk/riskinstances-list'
  },
  {
    path: '/risk/riskinstances-list',
    name: 'RiskInstancesList',
    component: RiskInstances
  },
  {
    path: '/risk/create-instance',
    name: 'CreateRiskInstance',
    component: CreateRiskInstance
  },
  {
    path: '/risk/resolution',
    name: 'RiskResolution',
    component: RiskResolution
  },
  {
    path: '/risk/workflow',
    name: 'RiskWorkflow',
    component: RiskWorkflow
  },
  {
    path: '/risk/scoring',
    name: 'RiskScoring',
    component: RiskScoring
  },
  {
    path: '/risk/scoring-details/:riskId',
    name: 'ScoringDetails',
    component: ScoringDetails,
    props: true
  },
  {
    path: '/risk/tailoring',
    name: 'RiskTailoring',
    component: TailoringRisk
  },
  {
    path: '/risk/riskkpi',
    name: 'RiskKPI',
    component: RiskKPI
  },
  {
    path: '/risk/baselkpis',
    name: 'BaselKPIs',
    component: BaselKPI
  },
  {
    path: '/view-risk/:id',
    name: 'ViewRisk',
    component: ViewRisk
  },
  {
    path: '/view-instance/:id',
    name: 'ViewInstance',
    component: ViewInstance
  },
 
  {
    path: '/help/contact-us',
    name: 'ContactUs',
    component: ContactUs,
    meta: { requiresAuth: true }
  },
  {
    path: '/help/getting-started',
    redirect: '/help/contact-us'
  },
  {
    path: '/help/faqs',
    name: 'FAQs',
    component: FAQs,
    meta: { requiresAuth: true }
    },
  {
    path: '/help/user-manual',
    name: 'UserManual',
    component: UserManual,
    meta: { requiresAuth: true }
  },
  {
    path: '/help/privacy-security',
    name: 'PrivacySecurity',
    component: PrivacySecurity,
    meta: { requiresAuth: true }
  },
  {
    path: '/help/help-us-improve',
    name: 'HelpUsImprove',
    component: HelpUsImprove,
    meta: { requiresAuth: true }
  },
  {
    path: '/help/acknowledgement',
    name: 'Acknowledgement',
    component: Acknowledgement,
    meta: { requiresAuth: true }
  },
 
 
 
  {
    path: '/framework-explorer/policies/:frameworkId',
    name: 'FrameworkPolicies',
    component: FrameworkPolicies,
    props: true
  },
  {
    path: '/policy/approval',
    name: 'PolicyApproval',
    component: PolicyApprover
  },
  {
    path: '/framework-approval',
    name: 'FrameworkApprover',
    component: FrameworkApprover
  },
  {
    path: '/framework-details/:frameworkId',
    name: 'FrameworkDetails',
    component: () => import('../components/Framework/FrameworkDetails.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/policy-details/:policyId',
    name: 'PolicyDetails',
    component: () => import('../components/Policy/PolicyDetails.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/compliance-details/:complianceId',
    name: 'ComplianceDetails',
    component: () => import('../components/Compliance/ComplianceDetails.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/framework-explorer',
    name: 'FrameworkExplorer',
    component: FrameworkExplorer
  },
  {
    path: '/policy/performance/dashboard',
    name: 'PolicyPerformanceDashboard',
    component: PolicyDashboard
  },
  {
    path: '/policy/performance/kpis',
    name: 'KPIDashboard',
    component: KPIDashboard
  },
  {
    path: '/framework-status-changes',
    name: 'StatusChangeRequests',
    component: StatusChangeRequests
  },
 
  {
    path: '/reviewer/confirmation/:auditId',
    name: 'ReviewConfirmation',
    component: ReviewConfirmation,
    props: true
  },
  {
    path: '/auditor/dashboard',
    name: 'AuditorDashboard',
    component: AuditorDashboard
  },
  {
    path: '/auditor/user-dashboard',
    name: 'AuditorUserDashboard',
    component: PerformanceDashboard
  },
  {
    path: '/auditor/reports',
    name: 'AuditReports',
    component: AuditReport
  },
  {
    path: '/audit-report/:id',
    name: 'AuditReportView',
    component: AuditReportView,
    props: true
  },
  {
    path: '/audit-findings/:id',
    name: 'AuditFindingDetailsView',
    component: AuditFindingDetailsView,
    props: true
  },
  {
    path: '/auditor/performance',
    component: PerformanceAnalysis,
    children: [
      {
        path: '',
        redirect: '/auditor/performance/dashboard'
      },
      {
        path: 'userdashboard',
        name: 'PerformanceDashboard',
        component: PerformanceDashboard
      },
      {
        path: 'kpi',
        name: 'KPIAnalysis',
        component: KPIAnalysis
      }
    ]
  },
 
  {
    path: '/compliance/create',
    name: 'CreateCompliance',
    component: CreateCompliance
  },
  {
    path: '/compliance/approver',
    name: 'ComplianceApprover',
    component: ComplianceApprover
  },
  {
    path: '/compliance/list',
    name: 'AllCompliance',
    component: AllCompliance,
    alias: '/control-management'
  },
  {
    path: '/compliance/audit-status',
    name: 'Compliances',
    component: Compliances
  },
  {
    path: '/compliance/audit-status/all',
    name: 'AllComplianceAudit',
    component: () => import('../components/Compliance/ComplianceAuditView.vue')
  },
  {
    path: '/compliance/audit-management',
    name: 'AuditManagement',
    component: () => import('../components/Compliance/AuditManagementView.vue')
  },
  {
    path: '/compliance/view/:type/:id/:name',
    name: 'ComplianceView',
    component: ComplianceView,
    props: true
  },
  {
    path: '/compliance/audit/:type/:id/:name',
    name: 'ComplianceAuditView',
    component: ComplianceAuditView,
    props: true
  },{
    path: '/compliance/user-dashboard',
    name: 'ComplianceDashboard',
    component: ComplianceDashboard
  },
  {
    path: '/compliance/kpi-dashboard',  
    name: 'ComplianceKPI',
    component: ComplianceKPI
  },
  {
    path: '/compliance/tailoring',
    name: 'ComplianceTailoring',
    component: ComplianceTailoring
  },
  {
    path: '/compliance/versioning',
    name: 'ComplianceVersioning',
    component: ComplianceVersioning
  },
  {
    path: '/compliance/popup-demo',
    name: 'PopupDemo',
    component: PopupDemo
  },
  {
    path: '/compliance/edit/:id',
    name: 'EditCompliance',
    component: EditCompliance
  },
  {
    path: '/compliance/copy/:id',
    name: 'CopyCompliance',
    component: CopyCompliance
  },
  {
    path: '/compliance/debug',
    name: 'ComplianceDebug',
    component: ComplianceDebug
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: Notifications,
    meta: { requiresAuth: true }
  },
  {
    path: '/user-profile',
    name: 'UserProfile',
    component: UserProfile,
    meta: { requiresAuth: true }
  },
  {
    path: '/access-denied',
    name: 'AccessDenied',
    component: AccessDenied,
    meta: { requiresAuth: true }
  },
  {
    path: '/rbac-test',
    name: 'RBACTest',
    component: RBACTest,
    meta: { requiresAuth: true }
  },
  {
    path: '/test-access-denied',
    name: 'TestAccessDenied',
    component: TestAccessDenied,
    meta: { requiresAuth: true }
  },
  {
    path: '/framework-migration',
    name: 'FrameworkMigration',
    component: () => import('../../vue/FrameworkMigration.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/framework-migration/comparison',
    name: 'FrameworkComparison',
    component: () => import('../../vue/FrameworkComparisonUpdated.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/framework-migration/migration',
    name: 'FrameworkMigrationProcess',
    component: () => import('../../vue/Migration.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/document-handling',
    name: 'DocumentHandling',
    component: DocumentHandling,
    meta: { requiresAuth: true }
  },
  {
    path: '/data-workflow',
    name: 'DataWorkflowTree',
    component: DataWorkflowTree,
    meta: { requiresAuth: true }
  },
  // EventHandling Routes
  {
    path: '/event-handling',
    name: 'EventHandlingLayout',
    component: Layout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/event-handling/dashboard'
      },
      {
        path: 'dashboard',
        name: 'EventsDashboard',
        component: EventsDashboard,
        meta: { requiresAuth: true }
      },
      {
        path: 'list',
        name: 'EventsList',
        component: EventsList,
        meta: { requiresAuth: true }
      },
      {
        path: 'queue',
        name: 'EventsQueue',
        component: EventsQueue,
        meta: { requiresAuth: true }
      },
      {
        path: 'calendar',
        name: 'EventsCalendar',
        component: EventsCalendar,
        meta: { requiresAuth: true }
      },
      {
        path: 'approval',
        name: 'EventsApproval',
        component: EventsApproval,
        meta: { requiresAuth: true }
      },
      {
        path: 'archived',
        name: 'ArchivedEvents',
        component: ArchivedEvents,
        meta: { requiresAuth: true }
      },
      {
        path: 'create',
        name: 'EventCreation',
        component: EventCreation,
        meta: { requiresAuth: true }
      },
      {
        path: 'details',
        name: 'EventDetails',
        component: () => import('../components/EventHandling/EventDetails.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'evidence-attachment',
        name: 'EvidenceAttachment',
        component: EvidenceAttachment,
        meta: { requiresAuth: true }
      }
    ]
  },
  {
    path: '/event-handling/view/:id',
    name: 'EventViewPopup',
    component: EventViewPopup,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/event-handling/approval/modal',
    name: 'ApprovalModal',
    component: ApprovalModal,
    meta: { requiresAuth: true }
  }
]
 
const router = createRouter({
  history: createWebHistory(),
  routes
})
 
// Navigation guard
router.beforeEach(async (to, from, next) => {
  console.log('🔐 Router guard checking:', { to: to.path, from: from.path })
 
  // Check if user is authenticated
  const accessToken = localStorage.getItem('access_token')
  const userId = localStorage.getItem('user_id')
  const isLoggedIn = localStorage.getItem('is_logged_in') === 'true'
 
  // Check token validity
  let isTokenValid = true
  if (accessToken) {
    try {
      const tokenPayload = JSON.parse(atob(accessToken.split('.')[1]))
      const currentTime = Math.floor(Date.now() / 1000)
      isTokenValid = tokenPayload.exp && tokenPayload.exp > currentTime
    } catch (error) {
      console.warn('⚠️ Invalid token format in router guard:', error)
      isTokenValid = false
    }
  }
 
  // User is authenticated if they have valid auth data, even if token is expired (will be refreshed)
  const hasAuthData = !!(accessToken && userId && isLoggedIn)
  const isAuthenticated = hasAuthData && (isTokenValid || accessToken) // Allow expired tokens for now
 
  console.log('🔐 Authentication status:', {
    hasToken: !!accessToken,
    hasUserId: !!userId,
    isLoggedIn: isLoggedIn,
    isTokenValid: isTokenValid,
    isAuthenticated: isAuthenticated
  })
 
  // If route requires authentication and user is not authenticated
  if (to.meta.requiresAuth && !isAuthenticated) {
    console.log('🚫 Access denied - redirecting to login')
    next('/login')
    return
  }
 
  // If user is authenticated and trying to access login page, redirect to home
  if (isAuthenticated && to.path === '/login') {
    console.log('🔄 User already authenticated - redirecting to home')
    next('/home')
    return
  }
 
  // Check RBAC permissions if route requires specific permissions
  if (to.meta.requiresPermission && isAuthenticated) {
    try {
      const { module, permission } = to.meta.requiresPermission
      console.log(`🔐 Checking permission: ${module}.${permission}`)
     
      // Import and check permission using RBAC service
      const rbacService = await import('@/services/rbacService.js')
      const hasPermission = await rbacService.default.checkPermission(module, permission)
     
      if (!hasPermission) {
        console.log(`🚫 Permission denied for ${module}.${permission}`)
       
        // Store access denied information
        const accessDeniedInfo = {
          feature: to.name || to.path,
          message: `You don't have permission to access ${to.name || 'this page'}. Required permission: ${module}.${permission}`,
          timestamp: new Date().toISOString(),
          url: to.fullPath,
          requiredPermission: `${module}.${permission}`
        }
        sessionStorage.setItem('accessDeniedInfo', JSON.stringify(accessDeniedInfo))
       
        next('/access-denied')
        return
      }
     
      console.log(`✅ Permission granted for ${module}.${permission}`)
    } catch (error) {
      console.error('🔐 Error checking permissions:', error)
     
      // Store access denied information
      const accessDeniedInfo = {
        feature: to.name || to.path,
        message: 'Error checking permissions. Please contact your administrator.',
        timestamp: new Date().toISOString(),
        url: to.fullPath,
        error: error.message
      }
      sessionStorage.setItem('accessDeniedInfo', JSON.stringify(accessDeniedInfo))
     
      next('/access-denied')
      return
    }
  }
 
  // Allow navigation
  next()
})
 
export default router
 