from django.urls import path, include

from rest_framework.routers import DefaultRouter

from django.http import HttpResponse

from .authentication import jwt_login, jwt_refresh, jwt_logout, jwt_verify, accept_consent, test_consent_auth, test_consent_simple

from .views import test_jwt_auth, list_users





from .views import serve_document



from .routes.EventHandling import event_views, riskavaire_integration
from .routes.Tree import tree

from .routes.DocumentHandling import document



from .routes.Policy.policy import (

    framework_list, framework_detail, policy_detail, policy_list,

    add_policy_to_framework, add_subpolicy_to_policy, subpolicy_detail,

    export_policies_to_excel, update_policy_approval, submit_policy_review,

    resubmit_policy_approval, resubmit_policy_by_id, list_users,

    get_framework_explorer_data, get_framework_policies, toggle_policy_status,

    get_framework_details, get_policy_details, all_policies_get_frameworks,

    all_policies_get_framework_versions, all_policies_get_framework_version_policies,

    all_policies_get_policies, all_policies_get_policy_versions,

    all_policies_get_subpolicies, all_policies_get_policy_version_subpolicies,

    all_policies_get_subpolicy_details, get_policy_dashboard_summary,

    get_policy_status_distribution, get_framework_status_distribution,

    get_reviewer_workload, get_recent_policy_activity, get_avg_policy_approval_time,

    get_policy_analytics, get_policy_kpis, acknowledge_policy,

    get_policies_by_framework, get_subpolicies_by_policy,

    get_latest_policy_approval, get_latest_policy_approval_by_role,

    get_latest_reviewer_version, submit_subpolicy_review, reject_subpolicy,

    resubmit_subpolicy, get_policy_version, get_subpolicy_version,

    submit_policy_approval_review, get_policy_version_history,

    list_policy_approvals_for_reviewer, list_policy_approvals_for_user,

    list_policy_approvals_for_reviewer_by_id, list_rejected_policy_approvals_for_user,

    get_policy_review_history, create_tailored_framework, create_tailored_policy,

    get_policy_categories, get_policy_subcategories, save_policy_category,

    get_entities, get_policy_compliance_stats, request_policy_status_change,

    approve_policy_status_change, get_policy_status_change_requests,

    get_policy_status_change_requests_by_user, get_policy_status_change_requests_by_reviewer,

    test_policy_status_debug, get_policy_extraction_progress,

    get_policy_counts_by_status, get_policies_paginated_by_status,

    upload_policy_document, get_departments, save_department,

    export_all_frameworks_policies, test_auth, test_submit_review, simple_test_endpoint, test_tailoring_permissions

)

from .routes.Policy.homePolices import get_policies_by_status, get_policy_details as get_home_policy_details

from .routes.UploadFramework.new_upload_framework import (

    upload_framework_file as new_upload_framework_file, 

    get_processing_status as new_get_processing_status, 

    get_sections as new_get_sections,

    get_sections_by_user as new_get_sections_by_user,

    list_user_folders as new_list_user_folders,

    load_default_data as new_load_default_data

)

from .routes.UploadFramework.upload_framework import (

    upload_framework_file, get_processing_status, get_sections,

    update_section, create_checked_structure,

    get_extracted_policies, direct_process_checked_sections,

    save_updated_policies, save_policies, save_single_policy,

    get_saved_excel_files, save_policy_details,

    save_complete_policy_package, save_framework_to_database

)

from .routes.uploadNist.checked_sections import (

    save_selected_sections, get_checked_sections, delete_checked_sections,

    process_checked_sections_pdfs_endpoint, get_extracted_policies_form_data,

    serve_checked_section_pdf

)

# New AI Upload API endpoints
from .routes.uploadNist.ai_upload_api import (
    upload_framework_pdf,
    start_pdf_processing,
    get_processing_status as ai_get_processing_status,
    get_extracted_data,
    list_user_folders as ai_list_user_folders
)

# Import the default data loader function
from .routes.uploadNist.default_data_loader import (
    load_default_data,
    get_default_data_sections,
    get_default_pdf_content,
    get_policies_for_section,
    get_subpolicies_for_policy
)

from .routes.Framework.frameworks import (

    create_framework_approval, get_framework_approvals, update_framework_approval,

    submit_framework_review, get_latest_framework_approval, get_rejected_frameworks_for_user,

    approve_reject_subpolicy_in_framework, approve_reject_policy_in_framework,

    approve_entire_framework_final, request_framework_status_change,

    approve_framework_status_change, get_status_change_requests,

    get_status_change_requests_by_user, get_status_change_requests_by_reviewer,

    update_existing_activeinactive_by_date, get_users_for_reviewer_selection,

    create_test_users, fix_framework_versions, test_user_id_extraction, test_framework_approval_routing, test_framework_approval_post_routing,

    get_approved_active_frameworks, set_selected_framework, get_selected_framework, test_session_debug

)

from .routes.Framework.framework_version import (

    create_framework_version as new_create_framework_version,

    get_framework_versions, get_all_framework_versions,

    activate_deactivate_framework_version, get_rejected_framework_versions,

    resubmit_rejected_framework, resubmit_framework_approval

)

from .routes.Policy.policy_version import (

    create_policy_version as policy_version_create,

    get_policy_versions as policy_version_get_versions,

    get_all_policy_versions as policy_version_get_all,

    get_rejected_policy_versions, activate_deactivate_policy,

    approve_policy_version

)

from .routes.Framework import framework_policy_counts

from .routes.Policy import policy_views









from .routes.Compliance import compliance_views

from .routes.Compliance import compliance





from .routes.Audit import audit_views, audit_report_views, audit_report_handlers

from .routes.Audit import ai_audit_views

from .routes.Audit import ai_audit_api

from .routes.Audit import ai_document_relevance

from .routes.Audit.ai_audit_api import (

    AIAuditDocumentUploadView, AIAuditDocumentsView, AIAuditStatusView

)

# Removed ai_auditor_recommendation_api import - module deleted as unused

from .routes.Audit.compliance_mapping_api import (

    map_document_to_compliance, get_policy_compliance_summary,

    map_audit_documents_to_compliance, get_compliance_requirements

)



from .routes.Audit.audit_views import (

    get_assign_data, load_review_data, load_latest_review_version,

    load_continuing_data, load_audit_continuing_data, save_audit_json_version,

    get_audit_compliances, get_subpolicies, export_audit_compliances

)

from .routes.Audit.assign_audit import (

    get_frameworks, get_policies, get_subpolicies, get_users_audit,

    create_audit, add_compliance_to_audit, get_compliance_count

)

from .routes.Audit.auditing import (

    get_audit_task_details, save_audit_version, send_audit_for_review,

    upload_evidence_to_s3

)

from .routes.Audit import reviewing,report_views

from .routes.Audit import kpi_functions









from .routes.Incident.incident_views import (

    FileUploadView, get_incident_counts as get_counts,

    create_workflow, create_incident_from_audit_finding

)

from .routes.Incident import incident_views







from .routes.Risk import risk_views, risk_kpi

from .routes.Risk.risk_views import (

    RiskViewSet, IncidentViewSet, ComplianceViewSet,

    RiskInstanceViewSet, export_risk_register_v2 ,export_compliance_management

)

from .routes.Risk.risk_kpi import upload_risk_evidence, delete_risk_evidence

from .routes.Risk import previous_version

from .routes.Risk.risk_dashboard_filter import (

    get_risk_dashboard_with_filters, get_risk_analytics_with_filters,

    get_risk_frameworks_for_filter, get_risk_policies_for_filter

)
from .routes.Risk.risk_ai_doc import (
    upload_and_process_risk_document, save_extracted_risks,
    test_ollama_connection, test_file_upload
)
from .routes.Risk.risk_instance_ai import (
    upload_and_process_risk_instance_document, save_extracted_risk_instances,
    test_ollama_connection_risk_instance
)
from .routes.Incident.incident_ai_import import (
    upload_and_process_incident_document, save_extracted_incidents,
    test_ollama_connection_incident
)





from . import views

from .routes.Audit import UserDashboard 

from .routes.Global import notification_service

from .routes.Global.notifications import (

    push_notification, get_notifications,

    mark_as_read, mark_all_as_read

)

from grc.rbac import views as rbac_views

from .routes.Global import rbac_test_views



from .routes.Global import user_profile

from .routes.Global.user_profile import *

# Import external integration views
from .routes.Integrations.event_integration import (
    get_external_applications,
    connect_external_application,
    disconnect_external_application,
    get_application_details,
    refresh_application_status,
    get_sync_logs,
    jira_oauth_callback,
    get_jira_projects,
    save_jira_project_details,
    disconnect_jira,
    get_jira_connection_status,
    get_jira_data,
    get_stored_projects_data,
    get_jira_project_details_from_db,
    get_all_users,
    assign_project_to_users,
    get_project_assignments,
    test_integration_auth
)

from .routes.Integrations.streamLine import (
    get_user_projects,
    get_project_details,
    get_user_statistics,
    save_task_action,
    get_user_task_actions
)
from .routes.Integrations.Bamboohr.bamboohr import (
    bamboohr_stored_data,
    bamboohr_employees,
    bamboohr_departments,
    bamboohr_sync_data,
    bamboohr_reports,
    bamboohr_oauth,
    bamboohr_oauth_callback
)













# 

# ============================================================================

# AUTHENTICATION URLs

# ============================================================================

auth_urlpatterns = [

    # Legacy session-based authentication (keeping for backward compatibility)

    path('login/', views.login_user, name='login'),

    path('logout/', views.logout_user, name='logout'),

    path('register/', views.register_user, name='register'),

    

    path('test-connection/', views.test_connection, name='test-connection'),

    path('login/', views.login_user, name='api-login'),

    path('logout/', views.logout_user, name='api-logout'),

    path('register/', views.register_user, name='api-register'),

    

    path('test-connection/', views.test_connection, name='api-test-connection'),

    path('send-otp/', views.send_otp, name='send-otp'),

    path('verify-otp/', views.verify_otp, name='verify-otp'),

    path('reset-password/', views.reset_password, name='reset-password'),

    path('get-user-email/', views.get_user_email_by_username, name='get-user-email'),

    path('rbac/roles/', views.get_rbac_roles, name='api-rbac-roles'),

    # path('departments/', views.get_departments, name='api-departments'),  # Removed duplicate

    # path('rbac/role-permissions/<str:role>/', views.get_role_permissions, name='api-role-permissions'),

    

    # JWT Authentication endpoints

    path('jwt/login/', jwt_login, name='jwt-login'),

    path('jwt/refresh/', jwt_refresh, name='jwt-refresh'),

    path('jwt/logout/', jwt_logout, name='jwt-logout'),

    path('jwt/verify/', jwt_verify, name='jwt-verify'),

    path('jwt/accept-consent/', accept_consent, name='accept-consent'),

    path('jwt/test-consent-auth/', test_consent_auth, name='test-consent-auth'),

    path('jwt/test-consent-simple/', test_consent_simple, name='test-consent-simple'),

    path('test-jwt-auth/', test_jwt_auth, name='test-jwt-auth'),

]



# ============================================================================

# RBAC (Role-Based Access Control) URLs

# ============================================================================

rbac_urlpatterns = [

    # Core RBAC endpoints

    path('rbac/user-permissions/', rbac_views.get_user_permissions, name='api-user-permissions'),

    path('rbac/user-role/', views.get_user_role_simple, name='api-user-role'),  # Simple endpoint from session

    path('user-role/', views.get_user_role_simple, name='user-role'),  # Frontend compatibility endpoint

    path('rbac/check-permission/', rbac_views.check_permission, name='rbac_check_permission'),

    # path('user-role-rbac/', rbac_views.get_user_role, name='api-user-role-rbac'),  # Keep original as backup

    path('rbac/users-for-dropdown/', views.get_users_for_dropdown_simple, name='api-users-for-dropdown'),  # Simple users dropdown

    # path('debug-permissions/', rbac_views.debug_user_permissions, name='api-debug-permissions'),

    # path('debug-rbac-data/', rbac_views.debug_rbac_data, name='api-debug-rbac-data'),

    # path('debug-auth-status/', rbac_views.debug_auth_status, name='api-debug-auth-status'),

    # path('debug-user-permissions/', incident_views.debug_user_permissions_endpoint, name='api-debug-user-permissions'),

    # path('test-user-permissions/', incident_views.test_user_permissions_comprehensive, name='api-test-user-permissions'),

    

    # # RBAC test endpoints

    # path('test-policy-view/', rbac_views.test_policy_view_permission, name='api-test-policy-view'),

    # path('test-policy-create/', rbac_views.test_policy_create_permission, name='api-test-policy-create'),

    # path('test-policy-approve/', rbac_views.test_policy_approve_permission, name='api-test-policy-approve'),

    # path('test-incident-view/', rbac_views.test_incident_view_permission, name='test-incident-view-permission'),

    # path('test-incident-create/', rbac_views.test_incident_create_permission, name='test-incident-create-permission'),

    # path('test-incident-assign/', rbac_views.test_incident_assign_permission, name='test-incident-assign-permission'),

    # path('test-any-permission/', rbac_views.test_any_permission, name='api-test-any-permission'),

    # path('test-all-permissions/', rbac_views.test_all_permissions, name='api-test-all-permissions'),

    # path('test-endpoint-permission/', rbac_views.test_endpoint_permission, name='api-test-endpoint-permission'),

    

    # User management test endpoints

    path('rbac/test-user-details/<int:user_id>/', views.get_user_details_by_id, name='test-user-details'),

    path('rbac/save-user-session/', views.save_user_session, name='save-user-session'),

    

    # RBAC Test endpoints for permission verification

    path('rbac/test/policy-view/', rbac_test_views.test_policy_view_permission, name='test-policy-view'),

    path('rbac/test/policy-create/', rbac_test_views.test_policy_create_permission, name='test-policy-create'),

    path('rbac/test/policy-edit/', rbac_test_views.test_policy_edit_permission, name='test-policy-edit'),

    path('rbac/test/audit-view/', rbac_test_views.test_audit_view_permission, name='test-audit-view'),

    path('rbac/test/audit-conduct/', rbac_test_views.test_audit_conduct_permission, name='test-audit-conduct'),

    path('rbac/test/audit-review/', rbac_test_views.test_audit_review_permission, name='test-audit-review'),

    path('rbac/test/public/', rbac_test_views.test_public_endpoint, name='test-public'),

]



# ============================================================================

# POLICY MODULE URLs

# ============================================================================

# EXPORT ENDPOINT FOR FRAMEWORK/POLICY

# from ...routes.Global.s3_fucntions import export_framework_policies



# urlpatterns += [

#     path('api/export-framework-policies/', export_framework_policies, name='export-framework-policies'),

#     path('api/export-risk-register/', export_risk_register, name='export-risk-register'),

# ]

policy_urlpatterns = [



    



    # Framework Management

    path('frameworks/', framework_list, name='framework-list'),

    path('frameworks/<int:pk>/', framework_detail, name='framework-detail'),

    path('frameworks/<int:framework_id>/create-version/', new_create_framework_version, name='create-framework-version'),

    path('frameworks/<int:framework_id>/export/', export_policies_to_excel, name='export-framework-policies'),

    path('frameworks/export-all/', export_all_frameworks_policies, name='export-all-frameworks-policies'),

    path('frameworks/<int:framework_id>/versions/', get_framework_versions, name='get-framework-versions'),

    path('framework-versions/', get_all_framework_versions, name='get-all-framework-versions'),

    path('frameworks/<int:framework_id>/toggle-active/', activate_deactivate_framework_version, name='activate-deactivate-framework-version'),

    path('framework-versions/rejected/', get_rejected_framework_versions, name='get-rejected-framework-versions'),

    path('framework-versions/rejected/<int:user_id>/', get_rejected_framework_versions, name='get-rejected-framework-versions-by-user'),

    path('frameworks/<int:framework_id>/resubmit-version/', resubmit_rejected_framework, name='resubmit-rejected-framework'),

    path('frameworks/<int:framework_id>/resubmit-approval/', resubmit_framework_approval, name='resubmit-framework-approval'),

    path('frameworks/approved-active/', get_approved_active_frameworks, name='get-approved-active-frameworks'),

    path('frameworks/set-selected/', set_selected_framework, name='set-selected-framework'),

    path('frameworks/get-selected/', get_selected_framework, name='get-selected-framework'),
    
    path('frameworks/test-session/', test_session_debug, name='test-session-debug'),

    

    # Policy Management

    path('policies/', policy_list, name='policy-list'),

    path('policies/<int:pk>/', policy_detail, name='policy-detail'),

    path('policies/<int:policy_id>/create-version/', policy_version_create, name='create-policy-version'),

    path('policies/<int:policy_id>/versions/', policy_version_get_versions, name='get-policy-versions'),

    path('policy-versions/', policy_version_get_all, name='get-all-policy-versions'),

    path('policies/<int:policy_id>/toggle-active/', activate_deactivate_policy, name='activate-deactivate-policy'),

    path('policies/<int:policy_id>/approve-version/', approve_policy_version, name='approve-policy-version'),

    path('policy-versions/rejected/', get_rejected_policy_versions, name='get-rejected-policy-versions'),

    path('policy-versions/rejected/<int:user_id>/', get_rejected_policy_versions, name='get-rejected-policy-versions-by-user'),

    path('policies/<int:policy_id>/resubmit-approval/', resubmit_policy_by_id, name='resubmit-policy-approval'),

    # path('policies/<int:policy_id>/debug-status/', debug_policy_status, name='debug-policy-status'),

    path('policy-approvals/<int:approval_id>/reject/', submit_policy_review, name='reject-policy-approval'),

    

    # Subpolicy Management

    path('subpolicies/<int:pk>/', subpolicy_detail, name='subpolicy-detail'),

    path('frameworks/<int:framework_id>/policies/', add_policy_to_framework, name='add-policy-to-framework'),

    path('frameworks/<int:framework_id>/policies/list/', compliance_views.get_policies, name='get-policies'),

    path('policies/<int:policy_id>/subpolicies/add/', add_subpolicy_to_policy, name='add-subpolicy-to-policy'),

    path('subpolicies/<int:pk>/review/', submit_subpolicy_review, name='submit-subpolicy-review'),

    path('subpolicies/<int:pk>/reject/', reject_subpolicy, name='reject-subpolicy'),

    path('subpolicies/<int:pk>/resubmit/', resubmit_subpolicy, name='resubmit-subpolicy'),

    

    # Policy Approvals

    path('policy-approvals/reviewer/', list_policy_approvals_for_reviewer, name='policy-approvals-for-reviewer'),

    path('policy-approvals/user/<int:user_id>/', list_policy_approvals_for_user, name='policy-approvals-for-user'),

    path('policy-approvals/reviewer/<int:user_id>/', list_policy_approvals_for_reviewer_by_id, name='policy-approvals-for-reviewer-by-id'),

    path('policy-counts/', get_policy_counts_by_status, name='get-policy-counts-by-status'),

    path('policies-paginated/', get_policies_paginated_by_status, name='get-policies-paginated-by-status'),

    path('policy-approvals/<int:approval_id>/', update_policy_approval, name='update_policy_approval'),

    path('policy-approvals/<int:approval_id>/review/', submit_policy_review, name='submit_policy_review'),

    path('policy-approvals/rejected/<int:user_id>/', list_rejected_policy_approvals_for_user, name='list-rejected-policy-approvals-for-user'),

    path('policy-approvals/resubmit/<int:approval_id>/', resubmit_policy_approval, name='resubmit-policy-approval-from-routes'),

    path('policies/<int:policy_id>/review-history/', get_policy_review_history, name='get-policy-review-history'),

    

    # Policy Users and Explorer

    path('policy-users/', list_users, name='list-users'),

    path('framework-explorer/', get_framework_explorer_data, name='framework-explorer'),

    path('frameworks/<int:framework_id>/policies-list/', get_framework_policies, name='framework-policies'),

    path('frameworks/<int:framework_id>/toggle-status/', request_framework_status_change, name='toggle-framework-status'),

    path('policies/<int:policy_id>/toggle-status/', toggle_policy_status, name='toggle-policy-status'),

    path('frameworks/<int:framework_id>/details/', get_framework_details, name='framework-details'),

    path('policies/<int:policy_id>/details/', get_policy_details, name='policy-details'),

    path('frameworks/<int:framework_id>/policy-counts/', policy_views.get_framework_policy_counts, name='framework-policy-counts'),

    

    # All Policies Views

    path('all-policies/frameworks/', all_policies_get_frameworks, name='all-policies-frameworks'),

    path('all-policies/frameworks/<int:framework_id>/versions/', all_policies_get_framework_versions, name='all-policies-framework-versions'),

    path('all-policies/framework-versions/<int:version_id>/policies/', all_policies_get_framework_version_policies, name='all-policies-framework-version-policies'),

    path('all-policies/policies/', all_policies_get_policies, name='all-policies-policies'),

    path('all-policies/policies/<int:policy_id>/versions/', all_policies_get_policy_versions, name='all-policies-policy-versions'),

    path('all-policies/subpolicies/', all_policies_get_subpolicies, name='all-policies-subpolicies'),

    path('all-policies/policy-versions/<int:version_id>/subpolicies/', all_policies_get_policy_version_subpolicies, name='all-policies-policy-version-subpolicies'),

    path('all-policies/subpolicies/<int:subpolicy_id>/', all_policies_get_subpolicy_details, name='all-policies-subpolicy-details'),

    

    # Policy Dashboard and Analytics

    path('policy-dashboard/', get_policy_dashboard_summary),

    path('policy-status-distribution/', get_policy_status_distribution),

    path('framework-status-distribution/', get_framework_status_distribution),

    path('reviewer-workload/', get_reviewer_workload),

    path('recent-policy-activity/', get_recent_policy_activity),

    path('avg-policy-approval-time/', get_avg_policy_approval_time),

    path('policy-analytics/', get_policy_analytics),

    path('api/policy-analytics/', get_policy_analytics, name='policy-analytics'),

    path('policy-kpis/', get_policy_kpis),

    

    # Policy Operations

    path('acknowledge-policy/<int:policy_id>/', acknowledge_policy, name='acknowledge-policy'),

    path('frameworks/<int:framework_id>/get-policies/', get_policies_by_framework, name='get-policies-by-framework'),

    path('policies/<int:policy_id>/get-subpolicies/', get_subpolicies_by_policy, name='get-subpolicies-by-policy'),

    path('policies/<int:policy_id>/version/', get_policy_version, name='get-policy-version'),

    path('subpolicies/<int:subpolicy_id>/version/', get_subpolicy_version, name='get-subpolicy-version'),

    path('policy-approvals/latest/<int:policy_id>/', get_latest_policy_approval, name='get-latest-policy-approval'),

    path('policy-approvals/latest-by-role/<int:policy_id>/<str:role>/', get_latest_policy_approval_by_role, name='get-latest-policy-approval-by-role'),

    path('policies/<int:policy_id>/reviewer-version/', get_latest_reviewer_version, name='get-policy-reviewer-version'),

    path('policies/<int:policy_id>/submit-review/', submit_policy_approval_review, name='submit-policy-approval-review'),

    path('policies/<int:policy_id>/version-history/', get_policy_version_history, name='get-policy-version-history'),

    path('test-auth/', test_auth, name='test-auth'),

    path('test-submit-review/<int:policy_id>/', test_submit_review, name='test-submit-review'),

    path('simple-test/<int:policy_id>/', simple_test_endpoint, name='simple-test-endpoint'),

    

    # Framework Approvals

    path('frameworks/<int:framework_id>/create-approval/', create_framework_approval, name='create-framework-approval'),

    path('frameworks/<int:framework_id>/approvals/', get_framework_approvals, name='get-framework-approvals'),

    path('frameworks/approvals/', get_framework_approvals, name='get-all-framework-approvals'),

    path('framework-approvals/<int:approval_id>/', update_framework_approval, name='update-framework-approval'),

    path('frameworks/<int:framework_id>/submit-review/', submit_framework_review, name='submit-framework-review'),

    path('framework-approvals/latest/<int:framework_id>/', get_latest_framework_approval, name='get-latest-framework-approval'),

    path('frameworks/<int:framework_id>/rejected/', get_rejected_frameworks_for_user, name='get-rejected-frameworks-for-user'),

    path('frameworks/rejected/', get_rejected_frameworks_for_user, name='get-all-rejected-frameworks'),

    

    # Tailoring

    path('tailoring/create-framework/', create_tailored_framework, name='create-tailored-framework'),

    path('tailoring/create-policy/', create_tailored_policy, name='create-tailored-policy'),

    path('tailoring/test-permissions/', test_tailoring_permissions, name='test-tailoring-permissions'),

    

    # Framework Operations

    path('frameworks/<int:framework_id>/policies/<int:policy_id>/subpolicies/<int:subpolicy_id>/approve-reject/', approve_reject_subpolicy_in_framework, name='approve-reject-subpolicy-in-framework'),

    path('frameworks/<int:framework_id>/policies/<int:policy_id>/approve-reject/', approve_reject_policy_in_framework, name='approve-reject-policy-in-framework'),

    path('frameworks/<int:framework_id>/approve-final/', approve_entire_framework_final, name='approve-entire-framework-final'),

    path('frameworks/<int:framework_id>/request-status-change/', request_framework_status_change, name='request-framework-status-change'),

    path('framework-approvals/<int:approval_id>/approve-status-change/', approve_framework_status_change, name='approve-framework-status-change'),

    path('framework-approvals/<int:approval_id>/test-routing/', test_framework_approval_routing, name='test-framework-approval-routing'),

    path('framework-approvals/<int:approval_id>/test-post-routing/', test_framework_approval_post_routing, name='test-framework-approval-post-routing'),

    path('frameworks/fix-versions/', fix_framework_versions, name='fix-framework-versions'),

    path('framework-status-change-requests/', get_status_change_requests, name='get-status-change-requests'),

    path('framework-status-change-requests/user/<int:user_id>/', get_status_change_requests_by_user, name='get-status-change-requests-by-user'),

    path('framework-status-change-requests/reviewer/<int:reviewer_id>/', get_status_change_requests_by_reviewer, name='get-status-change-requests-by-reviewer'),

    path('test-user-id-extraction/', test_user_id_extraction, name='test-user-id-extraction'),

    

    # Policy Categories and Status Changes

    path('policy-categories/', get_policy_categories, name='policy-categories'),

    path('policy-categories/save/', save_policy_category, name='save_policy_category'),

    path('policy-subcategories/', get_policy_subcategories, name='policy-subcategories'),

    path('policies/<int:policy_id>/request-status-change/', request_policy_status_change, name='request-policy-status-change'),

    path('policy-approvals/<int:approval_id>/approve-status-change/', approve_policy_status_change, name='approve-policy-status-change'),

    path('policy-status-change-requests/', get_policy_status_change_requests, name='get-policy-status-change-requests'),

    path('policy-status-change-requests/user/<int:user_id>/', get_policy_status_change_requests_by_user, name='get-policy-status-change-requests-by-user'),

    path('policy-status-change-requests/reviewer/<int:reviewer_id>/', get_policy_status_change_requests_by_reviewer, name='get-policy-status-change-requests-by-reviewer'),

    path('policy-status-change-requests-by-reviewer/', get_policy_status_change_requests_by_reviewer, name='get-policy-status-change-requests-by-reviewer'),

    path('policy-status-change-requests-by-reviewer/<int:reviewer_id>/', get_policy_status_change_requests_by_reviewer, name='get-policy-status-change-requests-by-reviewer-filtered'),

    path('policies/<int:policy_id>/test-debug/', test_policy_status_debug, name='test-policy-status-debug'),

    path('upload-policy-document/', upload_policy_document, name='upload-policy-document'),

    path('api/upload-policy-document/', upload_policy_document, name='api-upload-policy-document'),

    path('departments/', get_departments, name='api-get-departments'),  # Keep only one endpoint

    path('departments/save/', save_department, name='save-department'),

    path('departments/save/', save_department, name='api-save-department'),

    # Entities and Utilities

    path('entities/', get_entities, name='get-entities'),

    path('update-activeinactive-by-date/', update_existing_activeinactive_by_date, name='update-activeinactive-by-date'),

    path('users-for-reviewer-selection/', get_users_for_reviewer_selection, name='get-users-for-reviewer-selection'),

    path('status-change-requests-by-reviewer/', get_status_change_requests_by_reviewer, name='get-status-change-requests-by-reviewer'),

    path('status-change-requests-by-reviewer/<int:reviewer_id>/', get_status_change_requests_by_reviewer, name='get-status-change-requests-by-reviewer-filtered'),

    path('test-users/', create_test_users, name='create-test-users'),

    path('policies/<int:policy_id>/compliance-stats/', get_policy_compliance_stats, name='get-policy-compliance-stats'),

    path('home/policies-by-status/', get_policies_by_status, name='get-policies-by-status'),

    path('home/policy-details/<int:policy_id>/', get_home_policy_details, name='get-home-policy-details'),

    

    # Upload Framework Management (New Backend)

    path('upload-framework/', upload_framework_file, name='upload-framework'),

    path('upload-framework-new/', new_upload_framework_file, name='upload-framework-new'),



    path('processing-status/<str:task_id>/', get_processing_status, name='processing-status'),

    path('processing-status-new/<str:task_id>/', new_get_processing_status, name='processing-status-new'),

    path('get-sections/<str:task_id>/', get_sections, name='get-sections'),

    path('get-sections-new/<str:task_id>/', new_get_sections, name='get-sections-new'),

    path('get-sections-by-user/<str:userid>/', new_get_sections_by_user, name='get-sections-by-user'),

    path('list-user-folders/', new_list_user_folders, name='list-user-folders'),

    path('load-default-data/', new_load_default_data, name='load-default-data'),

    

    # Additional upload framework endpoints

    path('update-section/', update_section, name='update-section'),

    path('create-checked-structure/', create_checked_structure, name='create-checked-structure'),

    path('get-extracted-policies/<str:task_id>/', get_extracted_policies, name='get-extracted-policies'),

    path('direct-process-checked-sections/', direct_process_checked_sections, name='direct-process-checked-sections'),

    path('save-updated-policies/', save_updated_policies, name='save-updated-policies'),

    path('save-policies/', save_policies, name='save-policies'),

    path('save-single-policy/', save_single_policy, name='save-single-policy'),

    path('get-saved-excel-files/<str:task_id>/', get_saved_excel_files, name='get-saved-excel-files'),

    path('save-policy-details/', save_policy_details, name='save-policy-details'),

    path('save-complete-policy-package/', save_complete_policy_package, name='save-complete-policy-package'),

    path('save-framework-to-database/', save_framework_to_database, name='save-framework-to-database'),

    
    # ========================================================================
    # AI-POWERED UPLOAD FRAMEWORK - NEW API
    # ========================================================================
    # Step 1: Upload PDF and create user folder
    path('ai-upload/upload-pdf/', upload_framework_pdf, name='ai-upload-framework-pdf'),
    
    # Step 2-4: Process PDF (extract index, sections, policies)
    path('ai-upload/start-processing/', start_pdf_processing, name='ai-start-pdf-processing'),
    
    # Get processing status
    path('ai-upload/status/<str:task_id>/', ai_get_processing_status, name='ai-get-processing-status'),
    
    # Get extracted data for a user
    path('ai-upload/data/<str:userid>/', get_extracted_data, name='ai-get-extracted-data'),
    
    # List all user upload folders
    path('ai-upload/list-folders/', ai_list_user_folders, name='ai-list-user-folders'),
    
    # Default data loader endpoints
    path('ai-upload/load-default-data/', load_default_data, name='load-default-data-from-temp'),
    path('ai-upload/default-sections/<str:user_id>/', get_default_data_sections, name='get-default-data-sections'),
    path('ai-upload/default-pdf/<str:section_folder>/<str:control_id>/', get_default_pdf_content, name='get-default-pdf-content'),
    path('ai-upload/policies/<str:section_folder>/', get_policies_for_section, name='get-policies-for-section'),
    path('ai-upload/subpolicies/<str:section_folder>/<str:policy_id>/', get_subpolicies_for_policy, name='get-subpolicies-for-policy'),
    
    





]



# ============================================================================

# COMPLIANCE MODULE URLs

# ============================================================================

compliance_urlpatterns = [

    # Framework and Policy Data Access

    path('api/compliance/frameworks/', compliance_views.get_frameworks, name='get-frameworks'),

    path('api/compliance/frameworks/public/', compliance_views.get_frameworks_public, name='get-frameworks-public'),

    path('compliance/frameworks/public/', compliance_views.get_frameworks_public, name='get-frameworks-public-alias'),

    path('compliance/frameworks/', compliance_views.get_frameworks, name='api-get-frameworks'),

    path('compliance/frameworks/<int:framework_id>/policies/', compliance.get_policies, name='get-policies'),

    path('compliance/frameworks/<int:framework_id>/policies/list/', compliance_views.get_policies, name='api-get-policies'),

    path('compliance/policies/<int:policy_id>/subpolicies/', compliance.get_subpolicies, name='get-subpolicies'),

    path('compliance/policies/<int:policy_id>/subpolicies/', compliance_views.get_subpolicies, name='api-get-subpolicies'),

    # API-prefixed alias to match frontend usage

    path('api/compliance/policies/<int:policy_id>/subpolicies/', compliance.get_subpolicies, name='api-compliance-get-subpolicies'),

    path('api/compliance/view/<str:type>/<int:id>/', compliance.get_compliances_by_type, name='api-get-compliances-by-type'),

    path('compliance/view/<str:type>/<int:id>/', compliance.get_compliances_by_type, name='get-compliances-by-type'),

    

    # Compliance CRUD Operations

    path('compliance-create/', compliance_views.create_compliance, name='create-compliance'),

    path('api/compliance-create/', compliance_views.create_compliance, name='api-compliance-create'),

    path('compliance_edit/<int:compliance_id>/edit/', compliance_views.edit_compliance, name='edit-compliance'),

    path('api/compliance_edit/<int:compliance_id>/edit/', compliance_views.edit_compliance, name='api-edit-compliance'),

    path('clone-compliance/<int:compliance_id>/clone/', compliance_views.clone_compliance, name='clone-compliance'),

    # Add API-prefixed alias for clone endpoint to match frontend configuration

    path('api/clone-compliance/<int:compliance_id>/clone/', compliance_views.clone_compliance, name='api-clone-compliance'),

    path('compliance/<int:compliance_id>/framework-info/', compliance_views.get_compliance_framework_info, name='get-compliance-framework-info'),

    path('compliance/<int:compliance_id>/', compliance_views.get_compliance_details, name='get-compliance-details'),

    

    # Compliance by Type/Category

    path('subpolicies/<int:subpolicy_id>/compliances/', compliance_views.get_compliances_by_subpolicy, name='get-compliances-by-subpolicy'),

    path('api/subpolicies/<int:subpolicy_id>/compliances/', compliance_views.get_compliances_by_subpolicy, name='api-get-compliances-by-subpolicy'),

    

    path('compliances/framework/<int:framework_id>/', compliance_views.get_framework_compliances, name='get-framework-compliances'),

    path('compliances/policy/<int:policy_id>/', compliance_views.get_policy_compliances, name='get-policy-compliances'),

    path('compliances/subpolicy/<int:subpolicy_id>/', compliance_views.get_subpolicy_compliances, name='get-subpolicy-compliances'),

    path('compliances/<str:type>/<int:id>/', compliance_views.get_compliances_by_type, name='get_compliances_by_type'),

    

    # All Policies Views for Compliance

    path('compliance/all-policies/frameworks/', compliance_views.all_policies_get_frameworks, name='all-policies-get-frameworks'),

    path('compliance/all-policies/frameworks/', compliance_views.all_policies_get_frameworks, name='all-policies-frameworks'),

    path('compliance/all-policies/frameworks/<int:framework_id>/versions/', compliance_views.all_policies_get_framework_versions, name='all-policies-framework-versions'),

    path('compliance/all-policies/framework-versions/<int:version_id>/policies/', compliance_views.all_policies_get_framework_version_policies, name='all-policies-framework-version-policies'),

    path('compliance/all-policies/policies/', compliance_views.all_policies_get_policies, name='all-policies-get-policies'),

    path('compliance/all-policies/policies/', compliance_views.all_policies_get_policies, name='all-policies-policies'),

    path('api/compliance/all-policies/policies/<int:policy_id>/versions/', compliance_views.all_policies_get_policy_versions, name='all-policies-policy-versions'),

    path('compliance/all-policies/subpolicies/', compliance_views.all_policies_get_subpolicies, name='all-policies-get-subpolicies'),

    path('api/compliance/all-policies/subpolicies/', compliance_views.all_policies_get_subpolicies, name='all-policies-subpolicies'),

    path('api/compliance/all-policies/policy-versions/<int:version_id>/subpolicies/', compliance_views.all_policies_get_policy_version_subpolicies, name='all-policies-policy-version-subpolicies'),

    path('api/compliance/all-policies/subpolicies/<int:subpolicy_id>/', compliance_views.all_policies_get_subpolicy_details, name='all-policies-subpolicy-details'),

    path('compliance/all-policies/subpolicy/<int:subpolicy_id>/compliance-compliances/', compliance_views.all_policies_get_subpolicy_compliances, name='all-policies-get-subpolicy-compliances'),

    path('compliance/all-policies/subpolicies/<int:subpolicy_id>/compliances/', compliance_views.all_policies_get_subpolicy_compliances, name='all-policies-subpolicy-compliances'),

    path('compliance/all-policies/compliance/<int:compliance_id>/versions/', compliance_views.all_policies_get_compliance_versions, name='all-policies-get-compliance-versions'),

    path('api/compliance/all-policies/compliances/<int:compliance_id>/versions/', compliance_views.all_policies_get_compliance_versions, name='all-policies-compliance-versions'),

    

    # Compliance Approvals

    path('compliance/compliance-approvals/<int:approval_id>/review/', compliance_views.submit_compliance_review, name='submit_compliance_review'),

    path('compliance/compliance-approvals/resubmit/<int:approval_id>/', compliance_views.resubmit_compliance_approval, name='resubmit_compliance_approval'),

    path('compliance/versioning/', compliance_views.get_compliance_versioning, name='get-compliance-versioning'),

    path('compliance/policy-approvals-compliance/reviewer/', compliance_views.get_policy_approvals_by_reviewer, name='get-policy-approvals-by-reviewer'),

    path('compliance/policy-approvals-compliance/rejected/<int:reviewer_id>/', compliance_views.get_rejected_approvals, name='get-rejected-approvals'),

    

    # Version Control

    path('compliance/<int:compliance_id>/toggle-version/', compliance_views.toggle_compliance_version, name='toggle-compliance-version'),

    path('api/compliance/<int:compliance_id>/toggle-version/', compliance_views.toggle_compliance_version, name='api-toggle-compliance-version'),

    path('api/compliance/<int:compliance_id>/toggle/', compliance_views.toggle_compliance_version, name='api-toggle-compliance-alternative'),

    path('compliance/<int:compliance_id>/deactivate/', compliance_views.deactivate_compliance, name='deactivate-compliance'),

    path('compliance/deactivation/<int:approval_id>/approve/', compliance_views.approve_compliance_deactivation, name='approve-compliance-deactivation'),

    path('compliance/deactivation/<int:approval_id>/reject/', compliance_views.reject_compliance_deactivation, name='reject-compliance-deactivation'),

    

    # Dashboards and Analytics (with API-prefixed aliases for frontend)

    path('compliance/user-dashboard/', compliance_views.get_compliance_dashboard, name='compliance-dashboard'),

    path('compliance/user-dashboard/', compliance_views.get_compliance_dashboard, name='get-compliance-user-dashboard'),

    path('api/compliance/user-dashboard/', compliance_views.get_compliance_dashboard, name='api-compliance-user-dashboard'),

    path('compliance/dashboard-with-filters/', compliance.get_compliance_dashboard_with_filters, name='compliance-dashboard-with-filters'),

    path('api/compliance/dashboard-with-filters/', compliance.get_compliance_dashboard_with_filters, name='api-compliance-dashboard-with-filters'),

    path('compliance/test-framework-filter/', compliance.test_framework_filter, name='test-framework-filter'),

    path('api/compliance/test-framework-filter/', compliance.test_framework_filter, name='api-test-framework-filter'),



    path('compliance/kpi-dashboard/', compliance_views.get_compliance_kpi, name='get-compliance-kpi-dashboard'),

    path('api/compliance/kpi-dashboard/', compliance_views.get_compliance_kpi, name='api-get-compliance-kpi-dashboard'),



    path('compliance/kpi-dashboard/analytics/', compliance_views.get_compliance_analytics, name='compliance-analytics'),

    path('api/compliance/kpi-dashboard/analytics/', compliance_views.get_compliance_analytics, name='api-compliance-analytics'),

    path('compliance/kpi-dashboard/analytics/maturity-level/', compliance_views.get_maturity_level_kpi, name='get-maturity-level-kpi'),

    path('compliance/kpi-dashboard/analytics/non-compliance-count/', compliance_views.get_non_compliance_count, name='get-non-compliance-count'),

    path('compliance/kpi-dashboard/analytics/mitigated-risks-count/', compliance_views.get_mitigated_risks_count, name='get-mitigated-risks-count'),

    path('compliance/kpi-dashboard/analytics/automated-controls-count/', compliance_views.get_automated_controls_count, name='get-automated-controls-count'),

    path('compliance/kpi-dashboard/analytics/non-compliance-repetitions/', compliance_views.get_non_compliance_repetitions, name='get-non-compliance-repetitions'),

    path('compliance/kpi-dashboard/analytics/ontime-mitigation/', compliance_views.get_ontime_mitigation_percentage, name='get-ontime-mitigation-percentage'),

    path('compliance/kpi-dashboard/analytics/reputational-impact/', compliance_views.get_reputational_impact_assessment, name='get-reputational-impact'),

    path('compliance/kpi-dashboard/analytics/status-overview/', compliance_views.get_compliance_status_overview, name='get-compliance-status-overview'),

    path('compliance/kpi-dashboard/analytics/iso-framework-status/', compliance_views.get_iso_framework_compliance_status, name='get-iso-framework-compliance-status'),

    path('compliance/kpi-dashboard/analytics/policy-compliance-status/', compliance_views.get_policy_compliance_status, name='get-policy-compliance-status'),

    path('compliance/kpi-dashboard/analytics/remediation-cost/', compliance_views.get_remediation_cost_kpi, name='get-remediation-cost-kpi'),

    path('compliance/kpi-dashboard/analytics/non-compliant-incidents/', compliance_views.get_non_compliant_incidents_by_time, name='get-non-compliant-incidents'),

    

    # Export and Reports

    path('compliance/export/',

         compliance_views.export_compliances_post,

         name='export-compliances-post'),

    path('compliance/export/test/',

         compliance_views.test_compliance_export,

         name='test-compliance-export'),

    path('compliance/export/all-compliances/<str:export_format>/<str:item_type>/<int:item_id>/',

         compliance_views.export_compliances,

         name='export-all-compliances'),

    path('compliance/export/all-compliances/<str:export_format>/',

         compliance_views.export_compliances,

         name='export-all-compliances-legacy'),

    path('api/export/compliances/<str:format>/',

         compliance_views.export_audit_management_compliances,

         name='export-audit-management-compliances'),

    path('api/export/compliance-management/',

         compliance_views.export_compliance_management,

         name='export-compliance-management'),

    path('api/export/compliance-management/status/<int:export_id>/',

         compliance_views.get_export_status,

         name='get-export-status'),

    path('api/export/compliance-management/history/',

         compliance_views.list_export_history,

         name='list-export-history'),

    

    # Audit Information

    path('compliance/compliance/<int:compliance_id>/audit-info/',

         compliance_views.get_compliance_audit_info,

         name='get-compliance-audit-info'),

    

    # User Management

    path('compliance-users/', compliance_views.get_all_users, name='get-compliance-users'),

    path('api/compliance-users/', compliance_views.get_all_users, name='api-get-compliance-users'),

    

    # Categories

    path('categories/<str:source>/', compliance_views.get_category_values, name='get-category-values'),

    path('categories/add/', compliance_views.add_category_value, name='add-category-value'),

    path('categories/initialize/', compliance_views.initialize_default_categories, name='initialize-categories'),

    path('category-business-units/', compliance_views.get_category_business_units, name='get_category_business_units'),

    path('category-business-units/add/', compliance_views.add_category_business_unit, name='add_category_business_unit'),

    

    # Testing and Utilities

    path('test-notification/', compliance_views.test_notification, name='test-notification'),

    # Compliance Approvals for User Tasks

    path('compliance-approvals/user/<int:user_id>/', compliance_views.get_compliance_approvals_by_user, name='get_compliance_approvals_by_user'),

    path('compliance-approvals/reviewer/<int:user_id>/', compliance_views.get_compliance_approvals_by_reviewer, name='get_compliance_approvals_by_reviewer'),

    # Additional API endpoints for subpolicy integration

    path('compliance/policies/<int:policy_id>/subpolicies/add/', add_subpolicy_to_policy, name='api-add-subpolicy-to-policy'),

    # Audit Management - Get all compliances

    path('api/compliance/all-for-audit-management/', compliance_views.get_all_compliances_for_audit_management, name='get_all_compliances_for_audit_management'),

    path('compliance/all-for-audit-management/', compliance_views.get_all_compliances_for_audit_management, name='get_all_compliances_for_audit_management_alias'),

    path('api/compliance/all-for-audit-management/public/', compliance_views.get_all_compliances_for_audit_management_public, name='get_all_compliances_for_audit_management_public'),

    path('compliance/all-for-audit-management/public/', compliance_views.get_all_compliances_for_audit_management_public, name='get_all_compliances_for_audit_management_public_alias'),

    path('api/compliance/categories-for-audit-management/', compliance_views.get_categories_for_audit_management, name='get_categories_for_audit_management'),

    path('api/compliance/business-units-for-audit-management/', compliance_views.get_business_units_for_audit_management, name='get_business_units_for_audit_management'),

    path('api/compliance/debug-categories-business-units/', compliance_views.debug_categories_and_business_units, name='debug_categories_and_business_units'),

]



# ============================================================================

# AUDIT MODULE URLs

# ============================================================================

audit_urlpatterns = [

    # Data endpoints for assignment

    path('assign-data/', get_assign_data, name='get_assign_data'),

    path('create-audit/', create_audit, name='create_audit'),

    

    # Core Audit Management

    path('api/audits/', audit_views.get_all_audits, name='get_all_audits'),

    path('api/audits/public/', audit_views.get_all_audits_public, name='get_all_audits_public'),

    path('audits/public/', audit_views.get_all_audits_public, name='get_all_audits_public_alias'),

    path('my-audits/', audit_views.get_my_audits, name='get_my_audits'),

    path('my-reviews/', audit_views.get_my_reviews, name='get_my_reviews'),

    path('api/audits/<int:audit_id>/', audit_views.get_audit_details, name='get_audit_details'),

    path('audits/<int:audit_id>/status/', audit_views.update_audit_status, name='update_audit_status'),

    path('audits/<int:audit_id>/update-audit-review-status/', reviewing.update_audit_review_status, name='update_audit_review_status'),

    path('test-json-extraction/', reviewing.test_json_extraction, name='test_json_extraction'),

    path('api/audits/<int:audit_id>/get-status/', audit_views.get_audit_status, name='get_audit_status'),

    path('api/audits/<int:audit_id>/compliances/', get_audit_compliances, name='get_audit_compliances'),

    path('api/audits/<int:audit_id>/submit/', audit_views.submit_audit_findings, name='submit_audit_findings'),

    

    # Audit Version Management

    path('api/audits/<int:audit_id>/versions/', audit_views.get_audit_versions, name='get_audit_versions'),

    path('api/audits/<int:audit_id>/versions/<str:version>/', audit_views.get_audit_version_details, name='get_audit_version_details'),

    path('api/audits/<int:audit_id>/check-version/', audit_views.check_audit_version, name='check_audit_version'),

    path('api/audits/<int:audit_id>/save-audit-version/', save_audit_json_version, name='save_audit_json_version'),

    path('audits/<int:audit_id>/save-version/', save_audit_version, name='save_audit_version'),

    path('api/audits/<int:audit_id>/save-version/', save_audit_version, name='api_save_audit_version'),

    path('audits/<int:audit_id>/send-for-review/', send_audit_for_review, name='send_audit_for_review'),

    

    # Audit Findings

    path('api/audit-findings/<int:compliance_id>/', audit_views.update_audit_finding, name='update_audit_finding'),

    path('api/audit-findings/<int:compliance_id>/evidence/', audit_views.upload_evidence, name='upload_evidence'),

    path('api/upload-evidence/<int:compliance_id>/', audit_views.upload_evidence, name='upload_evidence_direct'),

    path('audit-findings-details/<int:audit_findings_id>/', audit_views.get_audit_finding_details, name='get_audit_finding_details'),

    

    # Audit Export

    path('api/export/audit-compliances/<str:format>/<str:item_type>/<int:item_id>/', audit_views.export_audit_compliances, name='export_audit_compliances'),

    

    # Compliance in Audit Context

    path('api/compliance/list/', audit_views.get_all_compliance, name='get_all_compliance'),

    path('api/subpolicies/<int:subpolicy_id>/compliance/', audit_views.get_compliance_by_subpolicy, name='get_compliance_by_subpolicy'),

    path('api/audits/<int:audit_id>/add-compliance/', add_compliance_to_audit, name='add_compliance_to_audit'),

    

    # Review Process

    path('audits/<int:audit_id>/save-review-progress/', audit_views.save_review_progress, name='save_review_progress'),

    path('api/audits/<int:audit_id>/load-review/', load_review_data, name='load_review_data'),

    path('api/audits/<int:audit_id>/load-latest-review-version/', load_latest_review_version, name='load_latest_review_version'),

    path('api/audits/<int:audit_id>/load-continuing-data/', load_continuing_data, name='load_continuing_data'),

    path('api/audits/<int:audit_id>/load-audit-continuing-data/', load_audit_continuing_data, name='load_audit_continuing_data'),

    

    # Audit Reports

    path('generate-audit-report/<int:audit_id>/', report_views.generate_audit_report, name='generate-audit-report'),

    path('audit-reports/', audit_report_views.get_audit_reports, name='get_audit_reports'),

    path('audit-reports/<int:audit_id>/versions/', audit_report_views.get_audit_report_versions, name='get_audit_report_versions'),

    path('audit-report/<int:audit_id>/', audit_report_views.get_audit_report, name='get_audit_report'),

    path('test-audit-reports/', audit_report_views.test_audit_reports, name='test_audit_reports'),

    path('audit-reports/<int:audit_id>/versions/<str:version>/delete/', audit_report_views.delete_audit_report_version, name='delete_audit_report_version'),

    path('audit-reports/<int:audit_id>/versions/<str:version>/s3-link/', audit_report_views.get_audit_report_s3_link, name='get_audit_report_s3_link'),

    path('audit-reports/check/', audit_report_handlers.check_audit_reports, name='check_reports'),

    path('audit-reports/details/', audit_report_handlers.get_report_details, name='get_report_details'),

    path('compliance-count/', get_compliance_count, name='get_compliance_count'),

    path('compliance-count/<int:policy_id>/', get_compliance_count, name='get_compliance_count_by_policy'),

    # API-prefixed aliases to match frontend requests

    path('api/compliance-count/', get_compliance_count, name='api_get_compliance_count'),

    path('api/compliance-count/<int:policy_id>/', get_compliance_count, name='api_get_compliance_count_by_policy'),

    

    # Business Units for Audit Module

    path('business-units/', incident_views.get_business_units, name='audit-business-units'),

    path('api/business-units/', incident_views.get_business_units, name='api-audit-business-units'),

    

    # Task Management

    path('audits/<int:audit_id>/task-details/', get_audit_task_details, name='get_audit_task_details'),

    path('audit-compliances/<int:audit_id>/', get_audit_compliances, name='get_audit_compliances'),

    path('audits/<int:audit_id>/compliances/', get_audit_compliances, name='get_audit_compliances_alt'),

    

    # S3 Upload

    path('upload-evidence-s3/', upload_evidence_to_s3, name='upload_evidence_to_s3'),

    

    # Audit Approval and Incident Creation

    path('approve-audit-and-create-incidents/<int:audit_id>/', report_views.approve_audit_and_create_incidents, name='approve_audit_and_create_incidents'),

    

    # KPI endpoints

    path('kpi/non-compliance/', kpi_functions.get_non_compliance_count, name='non_compliance_count'),

    path('kpi/audit-completion/', kpi_functions.get_audit_completion_metrics, name='audit_completion_metrics'),

    path('kpi/audit-cycle-time/', kpi_functions.get_audit_cycle_time, name='audit_cycle_time'),

    path('kpi/finding-rate/', kpi_functions.get_finding_rate, name='finding_rate'),

    path('kpi/time-to-close/', kpi_functions.get_time_to_close_findings, name='time_to_close_findings'),

    path('kpi/non-compliance-issues/', kpi_functions.get_non_compliance_issues, name='non_compliance_issues'),

    path('kpi/severity-distribution/', kpi_functions.get_severity_distribution, name='severity_distribution'),

    path('kpi/closure-rate/', kpi_functions.get_findings_closure_rate, name='findings_closure_rate'),

    path('kpi/evidence-completion/', kpi_functions.get_evidence_completion, name='evidence_completion'),

    path('kpi/report-timeliness/', kpi_functions.get_report_timeliness, name='report_timeliness'),

    path('kpi/compliance-readiness/', kpi_functions.get_compliance_readiness, name='compliance_readiness'),

    path('kpi/generate-sample-data/', kpi_functions.generate_sample_audit_data, name='generate_sample_audit_data'),

    

    # Dashboard endpoints

    path('dashboard/audit-completion-rate/', UserDashboard.get_audit_completion_rate, name='get_audit_completion_rate'),

    path('dashboard/total-audits/', UserDashboard.get_total_audits, name='get_total_audits'),

    path('dashboard/open-audits/', UserDashboard.get_open_audits, name='get_open_audits'),

    path('dashboard/completed-audits/', UserDashboard.get_completed_audits, name='get_completed_audits'),

    

    # Chart data endpoints

    path('dashboard/audit-completion-trend/', UserDashboard.audit_completion_trend, name='audit_completion_trend'),

    path('dashboard/audit-compliance-trend/', UserDashboard.audit_compliance_trend, name='audit_compliance_trend'),

    path('dashboard/audit-finding-trend/', UserDashboard.audit_finding_trend, name='audit_finding_trend'),

    path('dashboard/framework-performance/', UserDashboard.framework_performance, name='framework_performance'),

    path('dashboard/category-performance/', UserDashboard.category_performance, name='category_performance'),

    path('dashboard/status-distribution/', UserDashboard.status_distribution, name='status_distribution'),

    path('dashboard/recent-audit-activities/', UserDashboard.recent_audit_activities, name='recent_audit_activities'),

    

    # Framework and Policy Access for Audits

    path('audit/frameworks/', get_frameworks, name='get_audit_frameworks'),

    path('audit/policies/', get_policies, name='get_audit_policies'),

    path('audit/subpolicies/', get_subpolicies, name='get_audit_subpolicies'),

    path('audit/users/', get_users_audit, name='get_audit_users'),

    # API aliases for frontend compatibility

    path('api/subpolicies/', get_subpolicies, name='api_get_subpolicies'),

    # Migration and Debug endpoints

    path('api/add-majorminor-column/', audit_views.add_majorminor_column, name='add_majorminor_column'),

    path('api/fix-subpolicy-version/', audit_views.fix_subpolicy_version_field, name='fix_subpolicy_version_field'),

    path('api/fix-audit-table/', audit_views.fix_audit_table, name='fix_audit_table'),

    path('api/audits/<int:audit_id>/debug-status-transition/', audit_views.debug_audit_status_transition, name='debug_audit_status_transition'),

    path('api/debug/audit-version-schema/', audit_views.debug_audit_version_schema, name='debug_audit_version_schema'),



]



# ============================================================================

# INCIDENT MODULE URLs

# ============================================================================

incident_urlpatterns = [

    # Dashboard endpoints (moved to top for priority)

    path('incidents/dashboard/', incident_views.incident_dashboard, name='incident-dashboard'),

    path('incidents/dashboard/analytics/', incident_views.incident_analytics, name='incident-analytics'),

    

    # Framework endpoints for incident filtering (using existing compliance frameworks endpoint)

    # path('api/incidents/frameworks/', incident_views.get_incident_frameworks, name='api-incident-frameworks'),

    

    # API endpoints for dashboard KPIs and export

    path('api/dashboard-kpis/', incident_views.incident_dashboard, name='api-dashboard-kpis'),

    path('api/incidents/dashboard/', incident_views.incident_dashboard, name='api-incident-dashboard'),

    path('api/incidents/dashboard/analytics/', incident_views.incident_analytics, name='api-incident-analytics'),

    path('api/incident-export/', incident_views.export_incidents, name='api-incident-export'),

    path('api/incident-incidents/', incident_views.list_incidents, name='api-incident-incidents'),

    path('api/test-incident/', incident_views.test_incident_endpoint, name='test-incident-endpoint'),

    path('api/test-incident-count/', incident_views.test_incident_count, name='test-incident-count'),

    path('api/incidents-users/', incident_views.list_users, name='api-incidents-users'),

    path('api/incidents/create/', incident_views.create_incident, name='api-incidents-create'),

    path('api/incidents/export/', incident_views.export_incidents, name='api-incidents-export'),

    path('api/incidents/<int:incident_id>/', incident_views.incident_by_id, name='api-incident-by-id'),

    path('api/incidents/<int:incident_id>/update/', incident_views.update_incident_by_id, name='api-update-incident-by-id'),

    

    # Core Incident Management

    path('incident-incidents/', incident_views.list_incidents, name='api-list-incidents'),

    path('incidents/create/', incident_views.create_incident, name='api-create-incident'),

    path('incidents/create', incident_views.create_incident, name='api-create-incident-no-slash'),

    path('incident/create/', incident_views.create_incident, name='create-incident-singular'),

    path('incident/schedule-manual/', incident_views.schedule_manual_incident, name='schedule_manual_incident'),

    path('incident/reject/', incident_views.reject_incident, name='reject_incident'),

    path('incidents/create/', incident_views.create_incident, name='create-incident'),

    path('incidents/export/', incident_views.export_incidents, name='export-incidents'),

    path('incidents/recent/', incident_views.get_recent_incidents, name='recent-incidents'),

    path('api/incidents/recent/', incident_views.get_recent_incidents, name='api-recent-incidents'),

    

    # Incident Status and Assignment

    path('incidents/<int:incident_id>/status/', incident_views.update_incident_status, name='update-incident-status'),

    path('incidents/<int:incident_id>/assign/', incident_views.assign_incident, name='assign-incident'),

    path('api/incidents/<int:incident_id>/status/', incident_views.update_incident_status, name='api-update-incident-status'),

    path('api/incidents/<int:incident_id>/assign/', incident_views.assign_incident, name='api-assign-incident'),

    

    # Audit Findings Management

    path('audit-findings/', incident_views.get_audit_findings, name='get-audit-findings'),

    path('lastchecklistitemverified/', incident_views.audit_findings_list, name='audit-findings-list'),

    path('audit-findings/compliance/<int:compliance_id>/', incident_views.audit_finding_detail, name='audit-finding-detail'),

    path('audit-findings/incident/<int:incident_id>/', incident_views.audit_finding_incident_detail, name='audit-finding-incident-detail'),

    path('audit-findings/export/', incident_views.export_audit_findings, name='export-audit-findings'),

    

    # User Management  

    path('custom-users/', incident_views.list_users, name='custom-users'),

    path('api/custom-users/', incident_views.list_users, name='api-custom-users'),

    path('incident-users/', incident_views.list_users, name='list-users'),

    path('incidents-users/', incident_views.list_users, name='incidents-users'),

    

    # Workflow Management

    path('workflow/create/', incident_views.create_workflow, name='workflow-create'),

    path('workflow/assigned/', incident_views.list_assigned_findings, name='list-assigned-findings'),

    path('dashboard/incidents/', incident_views.combined_incidents_and_audit_findings, name='dashboard-incidents'),

    path('incident/from-audit-finding/', incident_views.create_incident_from_audit_finding, name='incident_from_audit_finding'),

    

    # Incident Metrics and KPIs

    path('incident/mttd/', incident_views.incident_mttd, name='incident-mttd'),

    path('incident/mttr/', incident_views.incident_mttr, name='incident_mttr'),

    path('incident/mttc/', incident_views.incident_mttc, name='incident-mttc'),

    path('incident/mttrv/', incident_views.incident_mttrv, name='incident-mttrv'),

    path('incident/first-response-time/', incident_views.first_response_time, name='first-response-time'),

    path('incident/incident-volume/', incident_views.incident_volume, name='incident-volume'),

    path('incident/escalation-rate/', incident_views.escalation_rate, name='escalation-rate'),

    path('incident/repeat-rate/', incident_views.repeat_rate, name='repeat-rate'),

    path('incident/metrics/', incident_views.incident_metrics, name='incident-metrics'),

    path('incidents/counts/', incident_views.get_incident_counts, name='incident-counts'),

    path('incident/count/', incident_views.incident_count, name='incident-count'),

    path('incident/by-severity/', incident_views.incidents_by_severity, name='incidents-by-severity'),

    path('incident/root-causes/', incident_views.incident_root_causes, name='incident-root-causes'),

    path('incident/origins/', incident_views.incident_origins, name='incident-origins'),

    path('incident/types/', incident_views.incident_types, name='incident-types'),

    path('incident/incident-cost/', incident_views.incident_cost, name='incident-cost'),

    path('incident/cost/', incident_views.incident_cost, name='incident-cost-alt'),

    path('incident/reopened-count/', incident_views.incident_reopened_count, name='incident-reopened-count'),

    path('incident/false-positive-rate/', incident_views.false_positive_rate, name='false-positive-rate'),

    path('incident/detection-accuracy/', incident_views.detection_accuracy, name='detection-accuracy'),

    path('incident/incident-closure-rate/', incident_views.incident_closure_rate, name='incident-closure-rate'),

    

    # Incident Compliance

    path('incident-compliances/', incident_views.get_compliances, name='get-compliances'),

    

    # Incident User Tasks

    path('user-incidents/<int:user_id>/', incident_views.user_incidents, name='user-incidents'),

    path('incident-reviewer-tasks/<int:user_id>/', incident_views.incident_reviewer_tasks, name='incident-reviewer-tasks'),

    path('incident-mitigations/<int:incident_id>/', incident_views.incident_mitigations, name='incident-mitigations'),

    path('assign-incident-reviewer/', incident_views.assign_incident_reviewer, name='assign-incident-reviewer'),

    path('incident-review-data/<int:incident_id>/', incident_views.incident_review_data, name='incident-review-data'),

    path('incident/<int:incident_id>/versions/', incident_views.incident_versions, name='incident-versions'),

    path('incident/<int:incident_id>/version/<str:version>/', incident_views.incident_version_detail, name='incident-version-detail'),

    path('audit-finding/<int:incident_id>/versions/', incident_views.audit_finding_versions, name='audit-finding-versions'),

    path('audit-finding/<int:incident_id>/version/<str:version>/', incident_views.audit_finding_version_detail, name='audit-finding-version-detail'),

    path('complete-incident-review/', incident_views.complete_incident_review, name='complete-incident-review'),

    path('submit-incident-assessment/', incident_views.submit_incident_assessment, name='submit-incident-assessment'),

    path('incident-approval-data/<int:incident_id>/', incident_views.incident_approval_data, name='incident-approval-data'),

    path('incidents/generate-analysis/', incident_views.generate_analysis, name='generate-analysis'),

    

    # Audit Finding User Tasks

    path('user-audit-findings/<int:user_id>/', incident_views.user_audit_findings, name='user-audit-findings'),

    path('audit-finding-reviewer-tasks/<int:user_id>/', incident_views.audit_finding_reviewer_tasks, name='audit-finding-reviewer-tasks'),

    path('audit-finding-mitigations/<int:incident_id>/', incident_views.audit_finding_mitigations, name='audit-finding-mitigations'),

    path('assign-audit-finding-reviewer/', incident_views.assign_audit_finding_reviewer, name='assign-audit-finding-reviewer'),

    path('audit-finding-review-data/<int:incident_id>/', incident_views.audit_finding_review_data, name='audit-finding-review-data'),

    path('complete-audit-finding-review/', incident_views.complete_audit_finding_review, name='complete-audit-finding-review'),

    path('submit-audit-finding-assessment/', incident_views.submit_audit_finding_assessment, name='submit-audit-finding-assessment'),

    # AI Audit Document Upload and Processing

    # AI Audit API endpoints - handle both string and integer audit IDs

    # Removed legacy FBV endpoints to avoid shadowing the class-based implementations

    # path('ai-audit/<str:audit_id>/documents/', ai_audit_views.get_audit_documents, name='get-audit-documents'),

    # path('ai-audit/<str:audit_id>/status/', ai_audit_views.get_ai_audit_status, name='get-ai-audit-status'),

    path('ai-audit/<str:audit_id>/review-finding/', ai_audit_views.review_ai_audit_findings, name='review-ai-audit-findings'),

    

    # AI Auditor Recommendation endpoints

    # Removed unused AI auditor recommendation endpoints - functions deleted

    

    # Compliance Mapping endpoints

    path('api/compliance-mapping/map-document/', map_document_to_compliance, name='map-document-to-compliance'),

    path('api/compliance-mapping/policy-summary/<int:policy_id>/', get_policy_compliance_summary, name='policy-compliance-summary'),

    path('api/compliance-mapping/audit-documents/<int:audit_id>/', map_audit_documents_to_compliance, name='map-audit-documents-to-compliance'),

    path('api/compliance-mapping/requirements/<int:policy_id>/', get_compliance_requirements, name='get-compliance-requirements'),

    

    # AI Audit API endpoints - Clean implementation

    path('ai-audit/<str:audit_id>/upload-document/', AIAuditDocumentUploadView.as_view(), name='api-upload-audit-document'),

    path('ai-audit/<str:audit_id>/documents/', AIAuditDocumentsView.as_view(), name='api-get-audit-documents'),

    path('ai-audit/<str:audit_id>/documents/<int:document_id>/map/', ai_audit_api.map_audit_document_api, name='api-map-audit-document'),

    path('ai-audit/<str:audit_id>/status/', AIAuditStatusView.as_view(), name='api-get-ai-audit-status'),

    path('ai-audit/<str:audit_id>/documents/<int:document_id>/check/', ai_audit_api.check_document_compliance, name='api-check-document-compliance'),

    path('ai-audit/<str:audit_id>/check-all/', ai_audit_api.check_all_documents_compliance, name='api-check-all-documents-compliance'),

    path('ai-audit/<str:audit_id>/start-processing/', ai_audit_api.start_ai_audit_processing_api, name='api-start-ai-audit-processing'),

    path('ai-audit/<str:audit_id>/download-report/', ai_audit_api.download_audit_report, name='api-download-audit-report'),

    path('ai-audit/<str:audit_id>/test-structured-compliance/', ai_audit_api.test_structured_compliance_api, name='api-test-structured-compliance'),

    path('ai-audit/<str:audit_id>/documents/<int:document_id>/', ai_audit_api.delete_audit_document_api, name='api-delete-audit-document'),

    
    # AI Incident Document Ingestion
    path('ai-incident-upload/', upload_and_process_incident_document, name='ai-incident-upload-document'),
    path('ai-incident-save/', save_extracted_incidents, name='ai-incident-save-incidents'),
    path('ai-incident-test/', test_ollama_connection_incident, name='ai-incident-test-ollama'),
    
    # AI Document Relevance Analysis

    # Note: The project-level urls.py already prefixes all routes with 'api/'.

    # Therefore this path MUST NOT start with 'api/' to avoid '/api/api/...'

    # and to match the frontend call to '/api/ai-audit/<audit_id>/analyze-document-relevance/'.

    path('ai-audit/<str:audit_id>/analyze-document-relevance/', ai_document_relevance.analyze_document_relevance, name='api-analyze-document-relevance'),

    # File Upload

    path('upload-incident-file/', FileUploadView.as_view(), name='upload-file'),

    path('upload-file/', FileUploadView.as_view(), name='api-upload-file'),

    path('upload-evidence-file/', incident_views.upload_evidence_file, name='upload-evidence-file'),

    path('upload-risk-evidence-file/', risk_views.upload_risk_evidence_file, name='upload-risk-evidence-file'),

    

    # Category and Business Unit Management

    path('categories/', incident_views.get_categories, name='get-categories'),

    path('business-units/', incident_views.get_business_units, name='get-business-units'),

    path('categories/add/', incident_views.add_category, name='add-category'),

    path('business-units/add/', incident_views.add_business_unit, name='add-business-unit'),

    path('incident-categories/', incident_views.get_incident_categories, name='get-incident-categories'),

    path('incident-categories/add/', incident_views.add_incident_category, name='add-incident-category'),

    

    # Test and Debug endpoints

    path('api/test-notification/', incident_views.test_notification, name='test-notification'),

    path('api/test-logging/', incident_views.test_logging, name='test-logging'),

    path('api/test-s3-integration/', incident_views.test_s3_integration, name='test-s3-integration'),

    path('seed-sample-data/', incident_views.seed_sample_data, name='seed-sample-data'),

    path('debug-category-data/', incident_views.debug_category_data, name='debug-category-data'),

]





# ============================================================================

# RISK MODULE URLs

# ============================================================================

risk_urlpatterns = [

    # Risk Dashboard with Filters

    path('risk/dashboard-with-filters/', get_risk_dashboard_with_filters, name='risk-dashboard-with-filters'),

    path('api/risk/dashboard-with-filters/', get_risk_dashboard_with_filters, name='api-risk-dashboard-with-filters'),

    path('risk/analytics-with-filters/', get_risk_analytics_with_filters, name='risk-analytics-with-filters'),

    path('api/risk/analytics-with-filters/', get_risk_analytics_with_filters, name='api-risk-analytics-with-filters'),

    path('risk/frameworks-for-filter/', get_risk_frameworks_for_filter, name='risk-frameworks-for-filter'),

    path('api/risk/frameworks-for-filter/', get_risk_frameworks_for_filter, name='api-risk-frameworks-for-filter'),

    path('risk/policies-for-filter/', get_risk_policies_for_filter, name='risk-policies-for-filter'),

    path('api/risk/policies-for-filter/', get_risk_policies_for_filter, name='api-risk-policies-for-filter'),

    

    # Risk ViewSet API URLs

    path('risks/', risk_views.RiskViewSet.as_view({'get': 'list', 'post': 'create'}), name='risk-list'),

    path('risks/<int:pk>/', risk_views.RiskViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'update', 'delete': 'destroy'}), name='risk-detail'),

    # API-prefixed aliases to match frontend

    path('api/risks/', risk_views.RiskViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-risk-list'),

    path('api/risks/<int:pk>/', risk_views.RiskViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'update', 'delete': 'destroy'}), name='api-risk-detail'),

    
    # AI-Powered Risk Document Ingestion URLs (NEW SIMPLIFIED PATHS)
    path('ai-risk-doc-upload/', upload_and_process_risk_document, name='ai-risk-upload-document'),
    path('ai-risk-save/', save_extracted_risks, name='ai-risk-save-risks'),
    path('ai-risk-test/', test_ollama_connection, name='ai-risk-test-ollama'),
    path('ai-risk-test-upload/', test_file_upload, name='ai-risk-test-upload'),
    
    # AI-Powered Risk Instance Document Ingestion URLs
    path('ai-risk-instance-upload/', upload_and_process_risk_instance_document, name='ai-risk-instance-upload-document'),
    path('ai-risk-instance-save/', save_extracted_risk_instances, name='ai-risk-instance-save-instances'),
    path('ai-risk-instance-test/', test_ollama_connection_risk_instance, name='ai-risk-instance-test-ollama'),
    
    # RiskInstance ViewSet URLs

    path('risk-instances/', risk_views.RiskInstanceViewSet.as_view({'get': 'list', 'post': 'create'}), name='risk-instance-list'),

    path('risk-instances/<int:pk>/', risk_views.RiskInstanceViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'update', 'delete': 'destroy'}), name='risk-instance-detail'),

    # API-prefixed aliases to match frontend

    path('api/risk-instances/', risk_views.RiskInstanceViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-risk-instance-list'),

    path('api/risk-instances/<int:pk>/', risk_views.RiskInstanceViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'update', 'delete': 'destroy'}), name='api-risk-instance-detail'),

    

    # Function-based risk instance creation (CSRF exempt)

    path('create-risk-instance/', risk_views.create_risk_instance, name='create-risk-instance'),

    path('api/create-risk-instance/', risk_views.create_risk_instance, name='api-create-risk-instance'),

    

    

    # Incident ViewSet URLs (Risk Module)

    path('incidents/', risk_views.IncidentViewSet.as_view({'get': 'list', 'post': 'create'}), name='incident-list'),

    path('incidents/<int:pk>/', risk_views.IncidentViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'update', 'delete': 'destroy'}), name='incident-detail'),

    

    # Compliance ViewSet URLs (Risk Module)

    path('compliances/', risk_views.ComplianceViewSet.as_view({'get': 'list', 'post': 'create'}), name='compliance-list'),

    path('compliances/<int:ComplianceId>/', risk_views.ComplianceViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'update', 'delete': 'destroy'}), name='compliance-detail'),

    

    # User Management

    path('users/', views.list_users, name='get-users'),

    path('api/users/', views.list_users, name='api-get-users'),

    path('risk-custom-users/', risk_views.get_custom_users, name='risk-custom-users'),

    path('risk-custom-users/<int:user_id>/', risk_views.get_custom_user, name='risk-custom-user'),

    path('user-risks/<int:user_id>/', risk_views.get_user_risks, name='user-risks'),

    path('user-notifications/<int:user_id>/', risk_views.get_user_notifications, name='user-notifications'),

    path('generate-test-notification/<int:user_id>/', risk_views.generate_test_notification, name='generate-test-notification'),

    

    # Risk Management

    path('risk/metrics', risk_views.risk_metrics, name='risk_metrics'),

    path('risk-workflow/', risk_views.risk_workflow, name='risk-workflow'),

    path('risk-assign/', risk_views.assign_risk_instance, name='risk-assign'),

    path('risk-update-status/', risk_views.update_risk_status, name='risk-update-status'),

    path('risk-mitigations/<int:risk_id>/', risk_views.get_risk_mitigations, name='risk-mitigations'),

    path('risk-update-mitigation/<int:risk_id>/', risk_views.update_risk_mitigation, name='risk-update-mitigation'),

    path('risk-form-details/<int:risk_id>/', risk_views.get_risk_form_details, name='risk-form-details'),

    path('risk/categories-for-dropdown/', risk_views.get_risk_categories_for_dropdown, name='risk_categories_for_dropdown'),

    path('risk/heatmap/', risk_views.get_risk_heatmap_data, name='risk_heatmap'),

    path('risk/heatmap/coordinates/<int:impact>/<int:likelihood>/', risk_views.get_risks_by_heatmap_coordinates, name='risk_by_heatmap_coordinates'),

    path('risk/trend-over-time/', risk_views.risk_trend_over_time, name='risk_trend_over_time'),

    path('risk/metrics-by-category/', risk_views.risk_metrics_by_category, name='risk_metrics_by_category'),

    path('risk/custom-analysis/', risk_views.custom_risk_analysis, name='risk_custom_analysis'),

    path('risk/by-category/<str:category>/', risk_views.get_risks_by_category, name='risk_by_category'),

    path('last-incident/', risk_views.last_incident, name='last-incident'),

    path('compliance-by-incident/<int:incident_id>/', risk_views.get_compliance_by_incident, name='compliance-by-incident'),

    path('risks-by-incident/<int:incident_id>/', risk_views.get_risks_by_incident, name='risks-by-incident'),

    path('risks-for-dropdown/', risk_views.get_all_risks_for_dropdown, name='risks-for-dropdown'),

    # API-prefixed alias to match frontend configuration

    path('api/risks-for-dropdown/', risk_views.get_all_risks_for_dropdown, name='api-risks-for-dropdown'),

    # Backward-compatible: support optional query segment for frontend path

    path('compliances-for-dropdown/', risk_views.get_all_compliances_for_dropdown, name='compliances-for-dropdown'),

    path('compliances-for-dropdown/<str:query>/', risk_views.get_all_compliances_for_dropdown, name='compliances-for-dropdown-with-query'),

    # API-prefixed aliases to match frontend configuration

    path('api/compliances-for-dropdown/', risk_views.get_all_compliances_for_dropdown, name='api-compliances-for-dropdown'),

    path('api/compliances-for-dropdown/<str:query>/', risk_views.get_all_compliances_for_dropdown, name='api-compliances-for-dropdown-with-query'),

    # path('users-for-dropdown/', risk_views.get_users_for_dropdown, name='users-for-dropdown'),  # Replaced with API version

    path('analyze-incident/', risk_views.analyze_incident, name='analyze-incident'),

    

    # Risk Reviewer Management

    path('assign-reviewer/', risk_views.assign_reviewer, name='assign-reviewer'),

    path('reviewer-tasks/<int:user_id>/', risk_views.get_reviewer_tasks, name='reviewer-tasks'),

    path('complete-review/', risk_views.complete_review, name='complete-review'),

    path('reviewer-comments/<int:risk_id>/', risk_views.get_reviewer_comments, name='reviewer-comments'),

    path('latest-review/<int:risk_id>/', risk_views.get_latest_review, name='latest-review'),

    path('get-assigned-reviewer/<int:risk_id>/', risk_views.get_assigned_reviewer, name='get-assigned-reviewer'),

    

    # Previous Version Management

    path('risk/<int:risk_id>/versions/', previous_version.get_all_versions, name='get-all-versions'),

    path('risk/<int:risk_id>/version/<str:version>/', previous_version.get_previous_version, name='get-previous-version'),

    path('risk/<int:risk_id>/compare/<str:version1>/<str:version2>/', previous_version.get_version_comparison, name='get-version-comparison'),





    # Risk Export and Reporting

    path('export-risk-register/', export_risk_register_v2, name='export-risk-register'),

    path('export-compliance-register/', export_compliance_management, name='export-compliance-register'),

    path('api/risk-register/export/', export_risk_register_v2, name='export-risk-register-v2'),

    path('api/export-risk-register/', export_risk_register_v2, name='export-risk-register-api'),

 

    # Mitigation Management

    path('update-mitigation-status/', risk_views.update_mitigation_status, name='update-mitigation-status'),

    

    # Logging

    path('logs/', risk_views.GRCLogList.as_view(), name='log-list'),

    path('logs/<int:pk>/', risk_views.GRCLogDetail.as_view(), name='log-detail'),

    

    # Risk KPI URLs

    path('risk/kpi-data/', risk_views.risk_kpi_data, name='risk_kpi_data'),

    path('risk/active-risks-kpi/', risk_views.active_risks_kpi, name='active_risks_kpi'),

    path('risk/exposure-trend/', risk_views.risk_exposure_trend, name='risk_exposure_trend'),

    path('risk/reduction-trend/', risk_views.risk_reduction_trend, name='risk_reduction_trend'),

    path('risk/high-criticality/', risk_views.high_criticality_risks, name='high_criticality_risks'),

    path('risk/mitigation-completion-rate/', risk_views.mitigation_completion_rate, name='mitigation_completion_rate'),

    path('risk/avg-remediation-time/', risk_views.avg_remediation_time, name='avg_remediation_time'),

    path('risk/recurrence-rate/', risk_views.recurrence_rate, name='recurrence_rate'),

    path('risk/avg-incident-response-time/', risk_views.avg_incident_response_time, name='avg_incident_response_time'),

    path('risk/mitigation-cost/', risk_views.mitigation_cost, name='mitigation_cost'),

    path('risk/identification-rate/', risk_views.risk_identification_rate, name='risk_identification_rate'),

    path('risk/due-mitigation/', risk_views.due_mitigation, name='due_mitigation'),

    path('risk/classification-accuracy/', risk_views.classification_accuracy, name='classification_accuracy'),

    path('risk/improvement-initiatives/', risk_views.improvement_initiatives, name='improvement_initiatives'),

    path('risk/impact/', risk_views.risk_impact, name='risk_impact'),

    path('risk/severity/', risk_views.risk_severity, name='risk_severity'),

    path('risk/exposure-score/', risk_views.risk_exposure_score, name='risk_exposure_score'),

    path('risk/resilience/', risk_views.risk_resilience, name='risk_resilience'),

    path('risk/assessment-frequency/', risk_views.risk_assessment_frequency, name='risk_assessment_frequency'),

    path('risk/assessment-consensus/', risk_views.risk_assessment_consensus, name='risk_assessment_consensus'),

    path('risk/approval-rate-cycle/', risk_views.risk_approval_rate_cycle, name='risk_approval_rate_cycle'),

    path('risk/register-update-frequency/', risk_views.risk_register_update_frequency, name='risk_register_update_frequency'),

    path('risk/recurrence-probability/', risk_views.risk_recurrence_probability, name='risk_recurrence_probability'),

    path('risk/tolerance-thresholds/', risk_views.risk_tolerance_thresholds, name='risk_tolerance_thresholds'),

    path('risk/appetite/', risk_views.risk_appetite, name='risk_appetite'),

    

    # Business Impacts and Categories

    path('business-impacts/', risk_views.get_business_impacts, name='get_business_impacts'),

    path('business-impacts/add/', risk_views.add_business_impact, name='add_business_impact'),

    path('risk-categories/', risk_views.get_risk_categories, name='get_risk_categories'),

    path('risk-categories/add/', risk_views.add_risk_category, name='add_risk_category'),

    # API-prefixed aliases for frontend

    path('api/business-impacts/', risk_views.get_business_impacts, name='api-get-business-impacts'),

    path('api/business-impacts/add/', risk_views.add_business_impact, name='api-add-business-impacts'),

    path('api/risk-categories/', risk_views.get_risk_categories, name='api-get-risk-categories'),

    path('api/risk-categories/add/', risk_views.add_risk_category, name='api-add-risk-category'),

    

    # Risk Department and Business Unit Filters

    path('risk-departments/', risk_views.get_risk_departments, name='get_risk_departments'),

    path('risk-business-units/', risk_views.get_risk_business_units, name='get_risk_business_units'),

    path('api/risk-departments/', risk_views.get_risk_departments, name='api-get-risk-departments'),

    path('api/risk-business-units/', risk_views.get_risk_business_units, name='api-get-risk-business-units'),

    

    # Compliance URLs (Risk Module)

    path('compliance/frameworks/', compliance.get_frameworks, name='get-frameworks'),

    path('compliance/frameworks/<int:framework_id>/policies/', compliance.get_policies, name='get-policies'),

    path('compliance/policies/<int:policy_id>/subpolicies/', compliance.get_subpolicies, name='get-subpolicies'),

    path('compliance/view/<str:type>/<int:id>/', compliance.get_compliances_by_type, name='get-compliances-by-type'),





]
# ============================================================================
# DATA WORKFLOW TREE URLs
# ============================================================================
tree_urlpatterns = [
    path('tree/frameworks/', tree.get_all_frameworks, name='tree-get-frameworks'),
    path('tree/frameworks/<int:framework_id>/policies/', tree.get_policies_by_framework, name='tree-get-policies'),
    path('tree/policies/<int:policy_id>/subpolicies/', tree.get_subpolicies_by_policy, name='tree-get-subpolicies'),
    path('tree/subpolicies/<int:subpolicy_id>/compliances/', tree.get_compliances_by_subpolicy, name='tree-get-compliances'),
    path('tree/compliances/<int:compliance_id>/risks/', tree.get_risks_by_compliance, name='tree-get-risks'),
    path('tree/hierarchy/', tree.get_tree_hierarchy, name='tree-get-hierarchy'),
]

event_handling_urlpatterns = [

    # Test endpoint

    path('events/test/', event_views.test_endpoint, name='test-event-endpoint'),

    # Event Management URLs

    path('events/', event_views.get_events, name='get-events'),

    path('events/document-handling/', event_views.get_document_handling_events, name='get-document-handling-events'),

    path('events/frameworks/', event_views.get_frameworks_for_events, name='get-frameworks-for-events'),

    path('events/modules/', event_views.get_modules_for_events, name='get-modules-for-events'),

    path('events/create-module/', event_views.create_module, name='create-module'),

    path('events/event-types-by-framework/', event_views.get_event_types_by_framework, name='get-event-types-by-framework'),

    path('events/dynamic-fields/', event_views.get_dynamic_fields_for_event, name='get-dynamic-fields-for-event'),

    path('events/create-event-type/', event_views.create_event_type, name='create-event-type'),

    path('events/records/', event_views.get_records_by_module, name='get-records-by-module'),

    path('events/templates/', event_views.get_event_templates, name='get-event-templates'),

    path('events/create/', event_views.create_event, name='create-event'),

    path('events/list/', event_views.get_events_list, name='get-events-list'),

    # Event Permissions URL

    path('events/permissions/', event_views.get_user_event_permissions, name='get-user-event-permissions'),

    # User Management URLs for Event Creation

    path('events/current-user/', event_views.get_current_user, name='get-current-user'),

    path('events/users-for-reviewer/', event_views.get_users_for_reviewer, name='get-users-for-reviewer'),

    # Calendar Events URL

    path('events/calendar/', event_views.get_events_for_calendar, name='get-events-for-calendar'),

    # Events Dashboard URL

    path('events/dashboard/', event_views.get_events_dashboard, name='get-events-dashboard'),

    # Event Approval/Rejection URLs (specific patterns first)

    path('events/<int:event_id>/approve/', event_views.approve_event, name='approve-event'),

    path('events/<int:event_id>/reject/', event_views.reject_event, name='reject-event'),

    path('events/<int:event_id>/update/', event_views.update_event, name='update-event'),

    path('events/<int:event_id>/archive/', event_views.archive_event, name='archive-event'),

    path('events/<int:event_id>/unarchive/', event_views.unarchive_event, name='unarchive-event'),

    path('events/<int:event_id>/delete-permanently/', event_views.delete_event_permanently, name='delete-event-permanently'),

    path('events/<int:event_id>/attach-evidence/', event_views.attach_evidence, name='attach-evidence'),

    # Generic event details URL (should be last)

    path('events/<int:event_id>/', event_views.get_event_details, name='get-event-details'),

    path('events/archived/', event_views.get_archived_events, name='get-archived-events'),

    path('events/archived-queue-items/', event_views.get_archived_queue_items, name='get-archived-queue-items'),

    # Create Events Table URL

    path('events/create-table/', event_views.create_events_table, name='create-events-table'),

    

    # RiskAvaire Integration URLs

    path('riskavaire/webhook/', riskavaire_integration.riskavaire_webhook, name='riskavaire-webhook'),

    path('riskavaire/check-triggers/', riskavaire_integration.check_automated_triggers, name='check-automated-triggers'),

    path('riskavaire/events/', riskavaire_integration.get_riskavaire_events, name='get-riskavaire-events'),

    

    # Integration Events URLs

    path('events/test-integration-db/', event_views.test_integration_db_connection, name='test-integration-db'),

    path('events/integration-events/', event_views.get_integration_events, name='get-integration-events'),

    path('events/create-from-integration/', event_views.create_event_from_integration, name='create-event-from-integration'),

    

    # S3 File Upload URLs

    path('s3/upload/', event_views.s3_upload_file, name='s3-upload-file'),

    path('s3/download/<str:s3_key>/<str:file_name>/', event_views.s3_download_file, name='s3-download-file'),

    path('s3/test-connection/', event_views.s3_test_connection, name='s3-test-connection'),

    

    # File Operations URLs

    path('file-operations/', event_views.get_file_operations, name='get-file-operations'),

    path('s3/check-file/<str:s3_key>/<str:file_name>/', event_views.s3_check_file_exists, name='s3-check-file-exists'),

    

    # Event Evidence endpoints

    path('events/<int:event_id>/evidence/upload/', event_views.upload_event_evidence, name='upload-event-evidence'),

    path('events/<int:event_id>/evidence/', event_views.get_event_evidence, name='get-event-evidence'),

    path('events/<int:event_id>/evidence/details/', event_views.get_event_evidence_details, name='get-event-evidence-details'),

    path('events/<int:event_id>/evidence/<str:evidence_id>/', event_views.delete_event_evidence, name='delete-event-evidence'),

    

    # Evidence linking endpoints for incidents

    path('incidents/link-evidence/', event_views.link_evidence_to_incident, name='link-evidence-to-incident'),

    path('incidents/<int:incident_id>/linked-evidence/', event_views.get_incident_linked_evidence, name='get-incident-linked-evidence'),

    path('incidents/<int:incident_id>/linked-evidence/<str:evidence_id>/documents/<int:document_index>/download/', event_views.download_linked_evidence_document, name='download-linked-evidence-document'),

    

    # Evidence linking endpoints for risks

    path('risks/link-evidence/', risk_views.link_evidence_to_risk, name='link-evidence-to-risk'),

    path('risks/test-link-evidence/', risk_views.test_link_evidence_endpoint, name='test-link-evidence'),

]



# ============================================================================

# NOTIFICATION URLs

# ============================================================================

notification_urlpatterns = [

    path('push-notification/', push_notification, name='push-notification'),

    path('api/push-notification/', push_notification, name='api-push-notification'),

    path('get-notifications/', get_notifications, name='get-notifications'),

    path('api/get-notifications/', get_notifications, name='api-get-notifications'),

    path('mark-as-read/', mark_as_read, name='mark-as-read'),

    path('api/mark-as-read/', mark_as_read, name='api-mark-as-read'),

    path('mark-all-as-read/', mark_all_as_read, name='mark-all-as-read'),

    path('api/mark-all-as-read/', mark_all_as_read, name='api-mark-all-as-read'),

]



# EXTERNAL INTEGRATIONS URLs
# ============================================================================
integration_urlpatterns = [
    # Test endpoint
    path('test-integration-auth/', test_integration_auth, name='test-integration-auth'),
    
    # External Applications Management
    path('external-applications/', get_external_applications, name='get-external-applications'),
    path('external-applications/connect/', connect_external_application, name='connect-external-application'),
    path('external-applications/disconnect/', disconnect_external_application, name='disconnect-external-application'),
    path('external-applications/<int:application_id>/', get_application_details, name='get-application-details'),
    path('external-applications/refresh-status/', refresh_application_status, name='refresh-application-status'),
    path('external-applications/<int:application_id>/sync-logs/', get_sync_logs, name='get-sync-logs'),
    
    # Jira-specific endpoints
    path('jira/oauth-callback/', jira_oauth_callback, name='jira-oauth-callback'),
    path('jira/projects/', get_jira_projects, name='get-jira-projects'),
    path('jira/project-details/', save_jira_project_details, name='save-jira-project-details'),
    path('jira/disconnect/', disconnect_jira, name='disconnect-jira'),
    path('jira/connection-status/', get_jira_connection_status, name='get-jira-connection-status'),
    path('jira/data/', get_jira_data, name='get-jira-data'),
    path('jira/stored-projects-data/', get_stored_projects_data, name='get-stored-projects-data'),
    path('jira/project-details-from-db/', get_jira_project_details_from_db, name='get-jira-project-details-from-db'),
    path('jira/users/', get_all_users, name='get-all-users'),
    path('jira/assign-project/', assign_project_to_users, name='assign-project-to-users'),
    path('jira/project-assignments/', get_project_assignments, name='get-project-assignments'),
    
    # Streamline endpoints
    path('streamline/user-projects/', get_user_projects, name='get-user-projects'),
    path('streamline/project-details/', get_project_details, name='get-project-details'),
    path('streamline/user-statistics/', get_user_statistics, name='get-user-statistics'),
    path('streamline/save-task-action/', save_task_action, name='save-task-action'),
    path('streamline/user-task-actions/', get_user_task_actions, name='get-user-task-actions'),
    
    # BambooHR endpoints
    path('bamboohr/oauth/', bamboohr_oauth, name='bamboohr-oauth'),
    path('bamboohr/oauth-callback/', bamboohr_oauth_callback, name='bamboohr-oauth-callback'),
    path('bamboohr/stored-data/', bamboohr_stored_data, name='bamboohr-stored-data'),
    path('bamboohr/employees/', bamboohr_employees, name='bamboohr-employees'),
    path('bamboohr/departments/', bamboohr_departments, name='bamboohr-departments'),
    path('bamboohr/sync-data/', bamboohr_sync_data, name='bamboohr-sync-data'),
    path('bamboohr/reports/', bamboohr_reports, name='bamboohr-reports'),
]

# ============================================================================
# COMBINE ALL URL PATTERNS
# ============================================================================

# COMBINE ALL URL PATTERNS

# ============================================================================

urlpatterns = [

    # ========================================================================

    # AUTHENTICATION & RBAC

    # ========================================================================

    *auth_urlpatterns,

    *rbac_urlpatterns,

    

    # ========================================================================

    # POLICY MODULE

    # ========================================================================

    *policy_urlpatterns,

    

    # ========================================================================

    # COMPLIANCE MODULE  

    # ========================================================================

    *compliance_urlpatterns,

    

    # ========================================================================

    # AUDIT MODULE

    # ========================================================================

    *audit_urlpatterns,

    

    # ========================================================================

    # INCIDENT MODULE

    # ========================================================================

    *incident_urlpatterns,

    

    # ========================================================================

    # RISK MODULE

    # ========================================================================

    *risk_urlpatterns,

    

    # ========================================================================

    # EVENT HANDLING MODULE

    # ========================================================================

    *event_handling_urlpatterns,

    
    # ========================================================================
    # DATA WORKFLOW TREE
    # ========================================================================
    *tree_urlpatterns,
    
    # Risk file upload endpoints

    path('upload-risk-evidence/', upload_risk_evidence, name='upload-risk-evidence'),

    path('delete-risk-evidence/<str:file_id>/', delete_risk_evidence, name='delete-risk-evidence'),

    

    # Risk Scoring endpoints

    path('risk-scoring/incident-names/', risk_kpi.get_incident_names_for_risk_scoring, name='get-incident-names-for-risk-scoring'),

    path('risk-scoring/compliance-names/', risk_kpi.get_compliance_names_for_risk_scoring, name='get-compliance-names-for-risk-scoring'),

    path('risk-scoring/business-units/', risk_kpi.get_business_units_for_risk_scoring, name='get-business-units-for-risk-scoring'),

    path('risk-scoring/instances-with-names/', risk_kpi.get_risk_instances_with_names, name='get-risk-instances-with-names'),

    

    # ========================================================================

    # NOTIFICATIONS

    # ========================================================================

    *notification_urlpatterns,

    
    # ========================================================================
    # EXTERNAL INTEGRATIONS
    # ========================================================================
    *integration_urlpatterns,
    
    # User Profile URLs

    path('user-profile/<int:user_id>/', views.get_user_profile, name='user_profile'),

    path('user-business-info/<int:user_id>/', views.get_user_business_info, name='user_business_info'),

    path('user-permissions/<int:user_id>/', views.get_user_permissions, name='user_permissions'),

    path('current-user/', user_profile.get_current_user, name='current-user'),



    # RBAC API endpoints (duplicate removed - now handled in rbac_urlpatterns)

    # path('api/rbac/user-permissions/', rbac_views.get_user_permissions, name='rbac_user_permissions'),

    # path('api/rbac/check-permission/', rbac_views.check_permission, name='rbac_check_permission'),

    

    # Checked sections endpoints

    path('api/checked-sections/save-selected-sections/', save_selected_sections, name='save-selected-sections'),

    path('api/checked-sections/get-checked-sections/<str:user_id>/', get_checked_sections, name='get-checked-sections'),

    path('api/checked-sections/delete-checked-sections/<str:user_id>/', delete_checked_sections, name='delete-checked-sections'),

    path('api/checked-sections/process-pdfs/', process_checked_sections_pdfs_endpoint, name='process-checked-sections-pdfs'),

    path('api/checked-sections/get-extracted-policies-form-data/<str:user_id>/', get_extracted_policies_form_data, name='get-extracted-policies-form-data'),

    path('api/checked-sections/pdf/<str:user_id>/<str:section_folder>/<str:control_id>/', serve_checked_section_pdf, name='serve-checked-section-pdf'),

   
    
    # ========================================================================
    
    # DOCUMENT HANDLING
    
    # ========================================================================
    
    # Document Handling endpoints
    path('documents/list/', document.get_documents, name='get-documents'),
    path('documents/counts/', document.get_document_counts, name='get-document-counts'),

    # Document endpoints
    path('documents/<str:doc_type>/', serve_document, name='serve-document'),

    # Versioned AI Audit Documents endpoint (uses corrected handler)
    path('ai-audit/v2/<str:audit_id>/documents/', AIAuditDocumentsView.as_view(), name='api-get-audit-documents-v2'),



]