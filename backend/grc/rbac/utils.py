"""
Enhanced RBAC Utilities for GRC System

This module provides comprehensive utilities for checking permissions using the new RBAC table schema.
Supports all modules: Policy, Compliance, Audit, Risk, and Incident.
"""

import logging
from django.utils import timezone
from ..models import RBAC

logger = logging.getLogger(__name__)

class RBACUtils:
    """
    Enhanced RBAC Utility class for permission checking using the new RBAC table schema
    """
    
    @staticmethod
    def get_user_id_from_request(request):
        """
        Get user_id from request.user (set by middleware) or JWT token/session
        Supports both JWT and session authentication
        """
        #logger.debug("[RBAC] Starting get_user_id_from_request")
        
        # First check if request.user is already set by middleware
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'UserId'):
            user_id = getattr(request.user, 'UserId', None)
            if user_id:
                #logger.info(f"[RBAC] Successfully extracted user_id from request.user: {user_id}")
                return user_id
        
        # If request.user doesn't have UserId, try to get it from the user object
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'id'):
            user_id = getattr(request.user, 'id', None)
            if user_id:
                #logger.info(f"[RBAC] Successfully extracted user_id from request.user.id: {user_id}")
                return user_id
        
        # Try JWT authentication as fallback
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                
                # Use the same JWT verification method as the authentication system
                from ..authentication import verify_jwt_token
                payload = verify_jwt_token(token)
                user_id = payload.get('user_id') if payload else None
                
                if user_id:
                    #logger.info(f"[RBAC] Successfully extracted user_id from JWT: {user_id}")
                    return user_id
                else:
                    logger.warning("[RBAC] No user_id found in JWT payload")
                    
        except Exception as e:
            logger.error(f"[RBAC] Error extracting user_id from JWT: {e}")
        
        # Fallback to session authentication
        try:
            user_id = request.session.get('user_id')
            if user_id:
                #logger.info(f"[RBAC] Successfully extracted user_id from session: {user_id}")
                return user_id
            else:
                logger.warning("[RBAC] No user_id found in session")
                
        except Exception as e:
            logger.error(f"[RBAC] Error extracting user_id from session: {e}")
        
        logger.warning("[RBAC] No user_id found in request.user, JWT token, or session")
        return None
    
    @staticmethod
    def get_user_rbac_record(user_id):
        """Get the RBAC record for a user with extensive debugging"""
        try:
            
            
            #logger.debug(f"[RBAC] Looking up RBAC record for user_id: {user_id}")
            
            rbac_record = RBAC.objects.filter(user=user_id, is_active='Y').first()
            
            if not rbac_record:
                logger.warning(f"[RBAC] No active RBAC record found for user {user_id}")
                # Try to find any record for debugging
                all_records = RBAC.objects.filter(user=user_id)
                if all_records.exists():
                    logger.debug(f"[RBAC] Found {all_records.count()} inactive records for user {user_id}")
                else:
                    logger.debug(f"[RBAC] No RBAC records at all for user {user_id}")
                return None
            
            #logger.info(f"[RBAC] Found active RBAC record for user {user_id}: role={rbac_record.role}")
            #logger.debug(f"[RBAC] User details - username: {rbac_record.username}, role: {rbac_record.role}")
            
            return rbac_record
            
        except Exception as e:
            logger.error(f"[RBAC] Error getting RBAC record for user {user_id}: {e}")
            return None
    
    @staticmethod
    def check_endpoint_permission(request, endpoint_name, required_permission=None):
        """
        Check if user has permission to access a specific endpoint with detailed debugging
        
        Args:
            request: Django request object
            endpoint_name: Name of the endpoint (e.g., 'list_incidents', 'create_incident')
            required_permission: Optional specific permission to check
        
        Returns:
            dict: {
                'allowed': bool,
                'user_id': int or None,
                'user_role': str or None,
                'user_username': str or None,
                'message': str,
                'debug_info': dict
            }
        """
        try:
            #logger.info(f"[RBAC] ===== ENDPOINT PERMISSION CHECK =====")
            #logger.info(f"[RBAC] Endpoint: {endpoint_name}")
            #logger.info(f"[RBAC] Required Permission: {required_permission}")
            #logger.info(f"[RBAC] Request Path: {request.path}")
            #logger.info(f"[RBAC] Request Method: {request.method}")
            
            user_id = RBACUtils.get_user_id_from_request(request)
            if not user_id:
                logger.warning(f"[RBAC] Access DENIED - No user_id in session for endpoint: {endpoint_name}")
                return {
                    'allowed': False,
                    'user_id': None,
                    'user_role': None,
                    'user_username': None,
                    'message': 'No user ID found in session',
                    'debug_info': {'session_available': hasattr(request, 'session')}
                }
            
            rbac_record = RBACUtils.get_user_rbac_record(user_id)
            if not rbac_record:
                logger.warning(f"[RBAC] Access DENIED - No RBAC record for user {user_id} on endpoint: {endpoint_name}")
                return {
                    'allowed': False,
                    'user_id': user_id,
                    'user_role': None,
                    'user_username': None,
                    'message': f'No RBAC record found for user {user_id}',
                    'debug_info': {'user_id': user_id}
                }
            
            # Define endpoint permission mappings for all modules
            endpoint_permissions = {
                # ===== INCIDENT MODULE ENDPOINTS =====
                'list_incidents': 'view_all_incident',
                'create_incident': 'create_incident', 
                'update_incident_status': 'edit_incident',
                'assign_incident': 'assign_incident',
                'incident_dashboard': 'view_all_incident',
                'incident_analytics': 'incident_performance_analytics',
                'export_incidents': 'view_all_incident',
                'get_recent_incidents': 'view_all_incident',
                'get_audit_findings': 'view_all_incident',
                'audit_findings_list': 'view_all_incident',
                'audit_finding_detail': 'view_all_incident',
                'audit_finding_incident_detail': 'view_all_incident',
                'export_audit_findings': 'view_all_incident',
                'schedule_manual_incident': 'create_incident',
                'reject_incident': 'edit_incident',
                'escalate_incident': 'escalate_to_risk',
                'user_incidents': 'view_all_incident',
                'incident_reviewer_tasks': 'evaluate_assigned_incident',
                'incident_mitigations': 'view_all_incident',
                'assign_incident_reviewer': 'assign_incident',
                'incident_review_data': 'evaluate_assigned_incident',
                'complete_incident_review': 'evaluate_assigned_incident',
                'submit_incident_assessment': 'edit_incident',
                'incident_approval_data': 'view_all_incident',
                'get_business_units': 'view_all_incident',  # Business units used across modules
                
                # ===== POLICY MODULE ENDPOINTS =====
                'framework_list': 'view_all_policy',
                'framework_detail': 'view_all_policy',
                'create_framework_version': 'create_framework',
                'export_policies_to_excel': 'view_all_policy',
                'policy_list': 'view_all_policy',
                'policy_detail': 'view_all_policy',
                'add_policy_to_framework': 'create_policy',
                'add_subpolicy_to_policy': 'create_policy',
                'get_policies_by_framework': 'view_all_policy',
                'get_subpolicies_by_policy': 'view_all_policy',
                'update_policy_approval': 'approve_policy',
                'submit_policy_review': 'approve_policy',
                'submit_policy_approval_review': 'approve_policy',
                'resubmit_policy_approval': 'approve_policy',
                'list_policy_approvals_for_reviewer': 'approve_policy',
                'subpolicy_detail': 'view_all_policy',
                'submit_subpolicy_review': 'approve_policy',
                'resubmit_subpolicy': 'approve_policy',
                'get_policy_kpis': 'policy_performance_analytics',
                'get_policy_analytics': 'policy_performance_analytics',
                'get_policy_dashboard_summary': 'view_all_policy',
                'get_policy_status_distribution': 'policy_performance_analytics',
                'get_reviewer_workload': 'policy_performance_analytics',
                'get_recent_policy_activity': 'view_all_policy',
                'get_avg_policy_approval_time': 'policy_performance_analytics',
                'get_framework_explorer_data': 'view_all_policy',
                'get_framework_policies': 'view_all_policy',
                'toggle_framework_status': 'edit_policy',
                'toggle_policy_status': 'edit_policy',
                'get_framework_details': 'view_all_policy',
                'get_policy_details': 'view_all_policy',
                'create_tailored_framework': 'create_framework',
                'create_tailored_policy': 'create_policy',
                'get_policy_version': 'view_all_policy',
                'get_subpolicy_version': 'view_all_policy',
                'get_policy_version_history': 'view_all_policy',
                'get_policy_categories': 'view_all_policy',
                'get_frameworks': 'view_all_policy',  # Also used in policy module
                
                # ===== COMPLIANCE MODULE ENDPOINTS (5 MAIN FEATURES) =====
                
                # CreateCompliance endpoints
                'create_compliance': 'create_compliance',
                'clone_compliance': 'create_compliance',
                'add_category_value': 'create_compliance',
                'initialize_default_categories': 'create_compliance',
                'add_category_business_unit': 'create_compliance',
                
                # EditCompliance endpoints
                'edit_compliance': 'edit_compliance',
                'toggle_compliance_version': 'edit_compliance',
                'deactivate_compliance': 'edit_compliance',
                
                # ApproveCompliance endpoints
                'submit_compliance_review': 'approve_compliance',
                'resubmit_compliance_approval': 'approve_compliance',
                'get_policy_approvals_by_reviewer': 'approve_compliance',
                'get_rejected_approvals': 'approve_compliance',
                'approve_compliance_deactivation': 'approve_compliance',
                'reject_compliance_deactivation': 'approve_compliance',
                
                # ViewAllCompliance endpoints
                'get_compliance_dashboard': 'view_all_compliance',
                'get_compliances_by_subpolicy': 'view_all_compliance',
                'get_compliance_versioning': 'view_all_compliance',
                'get_compliance_details': 'view_all_compliance',
                'get_compliance_framework_info': 'view_all_compliance',
                'export_compliances': 'view_all_compliance',
                'get_subpolicy_compliances': 'view_all_compliance',
                'get_framework_compliances': 'view_all_compliance',
                'get_policy_compliances': 'view_all_compliance',
                'get_compliances_by_type': 'view_all_compliance',
                'get_category_values': 'view_all_compliance',
                'get_category_business_units': 'view_all_compliance',
                'test_notification': 'view_all_compliance',
                'get_frameworks': 'view_all_compliance',
                'get_policies': 'view_all_compliance',
                'get_subpolicies': 'view_all_compliance',
                'get_all_users': 'view_all_compliance',
                'all_policies_get_frameworks': 'view_all_compliance_or_incident',
                'all_policies_get_framework_version_policies': 'view_all_compliance_or_incident',
                'all_policies_get_policies': 'view_all_compliance_or_incident',
                'all_policies_get_subpolicies': 'view_all_compliance_or_incident',
                'all_policies_get_subpolicy_details': 'view_all_compliance_or_incident',
                'all_policies_get_framework_versions': 'view_all_compliance_or_incident',
                'all_policies_get_policy_version_subpolicies': 'view_all_compliance_or_incident',
                'all_policies_get_subpolicy_compliances': 'view_all_compliance_or_incident',
                'all_policies_get_compliance_versions': 'view_all_compliance_or_incident',
                'get_compliance_audit_info': 'view_all_compliance',
                'get_frameworks': 'view_all_compliance',  # Also used in compliance module
                
                # CompliancePerformanceAnalytics endpoints
                'get_compliance_analytics': 'compliance_performance_analytics',
                'get_compliance_kpi': 'compliance_performance_analytics',
                'get_maturity_level_kpi': 'compliance_performance_analytics',
                'get_non_compliance_count': 'compliance_performance_analytics',
                'get_mitigated_risks_count': 'compliance_performance_analytics',
                'get_automated_controls_count': 'compliance_performance_analytics',
                'get_non_compliance_repetitions': 'compliance_performance_analytics',
                'get_ontime_mitigation_percentage': 'compliance_performance_analytics',
                'get_compliance_status_overview': 'compliance_performance_analytics',
                'get_reputational_impact_assessment': 'compliance_performance_analytics',
                'get_remediation_cost_kpi': 'compliance_performance_analytics',
                'get_non_compliant_incidents_by_time': 'compliance_performance_analytics',
                'save_policy_category': 'create_policy',
                'acknowledge_policy': 'view_all_policy',
                'list_users': 'view_all_policy',
                
                # ===== AUDIT MODULE ENDPOINTS =====
                # Basic audit operations
                'get_all_audits': 'assign_audit',
                'get_my_audits': 'conduct_audit',
                'get_my_reviews': 'review_audit',
                'get_audit_details': 'view_audit_reports',
                'update_audit_status': 'conduct_audit',
                'submit_audit_findings': 'conduct_audit',
                'get_audit_versions': 'view_audit_reports',
                'save_audit_version': 'conduct_audit',
                'send_audit_for_review': 'conduct_audit',
                'update_audit_finding': 'conduct_audit',
                'upload_evidence': 'conduct_audit',
                'get_compliance_by_subpolicy': 'view_audit_reports',
                'add_compliance_to_audit': 'assign_audit',
                'save_review_progress': 'review_audit',
                'load_review_data': 'review_audit',
                'generate_audit_report': 'view_audit_reports',
                'get_audit_reports': 'view_audit_reports',
                
                # Audit assignment and creation
                'get_frameworks': 'assign_audit',
                'get_policies': 'assign_audit',
                'get_subpolicies': 'assign_audit',
                'get_users_audit': 'assign_audit',
                'create_audit': 'assign_audit',
                'get_assign_data': 'assign_audit',
                'get_compliance_count': 'assign_audit',
                
                # Audit assignment and creation
                'get_frameworks': 'assign_audit',
                'get_policies': 'assign_audit',
                'get_subpolicies': 'assign_audit',
                'get_users_audit': 'assign_audit',
                'create_audit': 'assign_audit',
                'get_assign_data': 'assign_audit',
                'get_compliance_count': 'assign_audit',
                
                # Audit task management
                'get_audit_task_details': 'conduct_audit',
                'get_audit_compliances': 'conduct_audit',
                'get_audit_status': 'conduct_audit',
                'check_audit_version': 'conduct_audit',
                'save_audit_json_version': 'conduct_audit',
                'upload_evidence_to_s3': 'conduct_audit',
                'load_continuing_data': 'conduct_audit',
                'load_audit_continuing_data': 'conduct_audit',
                'get_latest_reviewer_data': 'conduct_audit',
                'load_audit_with_reviewer_feedback': 'conduct_audit',
                
                # Audit review process
                'load_latest_review_version': 'review_audit',
                'update_audit_review_status': 'review_audit',
                'get_empty_review_structure': 'review_audit',
                'save_review_json': 'review_audit',
                'create_review_version': 'review_audit',
                'complete_audit_review': 'review_audit',
                'approve_audit_and_create_incidents': 'review_audit',
                
                # Audit report generation and management
                'get_audit_report_versions': 'view_audit_reports',
                'delete_audit_report_version': 'view_audit_reports',
                'get_audit_report_s3_link': 'view_audit_reports',
                'check_audit_reports': 'view_audit_reports',
                'get_report_details': 'view_audit_reports',
                
                # Audit analytics and KPIs
                'get_non_compliance_count': 'audit_performance_analytics',
                'get_audit_completion_metrics': 'audit_performance_analytics',
                'get_audit_cycle_time': 'audit_performance_analytics',
                'get_finding_rate': 'audit_performance_analytics',
                'get_time_to_close_findings': 'audit_performance_analytics',
                'get_non_compliance_issues': 'audit_performance_analytics',
                'get_severity_distribution': 'audit_performance_analytics',
                'get_findings_closure_rate': 'audit_performance_analytics',
                'get_evidence_completion': 'audit_performance_analytics',
                'get_report_timeliness': 'audit_performance_analytics',
                'get_compliance_readiness': 'audit_performance_analytics',
                
                # Audit dashboard endpoints
                'get_audit_completion_rate': 'audit_performance_analytics',
                'get_total_audits': 'assign_audit',
                'get_open_audits': 'assign_audit',
                'get_completed_audits': 'assign_audit',
                'audit_completion_trend': 'audit_performance_analytics',
                'audit_compliance_trend': 'audit_performance_analytics',
                'audit_finding_trend': 'audit_performance_analytics',
                'framework_performance': 'audit_performance_analytics',
                'category_performance': 'audit_performance_analytics',
                'status_distribution': 'audit_performance_analytics',
                'recent_audit_activities': 'assign_audit',
                
                # Audit maintenance and debug endpoints
                'add_majorminor_column': 'assign_audit',
                'fix_subpolicy_version_field': 'assign_audit',
                'fix_audit_table': 'assign_audit',
                'debug_audit_status_transition': 'conduct_audit',
                'debug_audit_version_schema': 'conduct_audit',
                'debug_audit_versions': 'conduct_audit',
                
                # ===== RISK MODULE ENDPOINTS =====
                'risk_workflow': 'view_all_risk',
                'assign_risk_instance': 'assign_risk',
                'update_risk_status': 'edit_risk',
                'get_risk_mitigations': 'view_all_risk',
                'update_risk_mitigation': 'edit_risk',
                'assign_reviewer': 'assign_risk',
                'get_reviewer_tasks': 'evaluate_assigned_risk',
                'complete_review': 'evaluate_assigned_risk',
                'get_reviewer_comments': 'view_all_risk',
                'update_mitigation_status': 'edit_risk',
                'analyze_incident': 'create_risk',
                
                # ===== COMPLIANCE MODULE ENDPOINTS =====
                'create_compliance': 'create_compliance',
                'edit_compliance': 'edit_compliance',
                'get_compliance_details': 'view_all_compliance',
                'get_compliance_dashboard': 'view_all_compliance',
                'get_compliance_analytics': 'compliance_performance_analytics',
                'submit_compliance_review': 'approve_compliance',
                'resubmit_compliance_approval': 'approve_compliance',
                'export_compliances': 'view_all_compliance',
            }
            
            # Use provided permission or look up from mapping
            permission_to_check = required_permission or endpoint_permissions.get(endpoint_name)
            
            if not permission_to_check:
                logger.warning(f"[RBAC] No permission mapping found for endpoint: {endpoint_name}")
                #logger.info(f"[RBAC] Available endpoints: {list(endpoint_permissions.keys())[:10]}...") # Show first 10
                return {
                    'allowed': False,
                    'user_id': user_id,
                    'user_role': rbac_record.role,
                    'user_username': rbac_record.username,
                    'message': f'No permission mapping found for endpoint: {endpoint_name}',
                    'debug_info': {'endpoint_name': endpoint_name, 'available_mappings_count': len(endpoint_permissions)}
                }
            
            # Check the permission (handle composite permissions)
            if permission_to_check == 'view_all_compliance_or_incident':
                has_permission = rbac_record.view_all_compliance or rbac_record.view_all_incident
            else:
                has_permission = getattr(rbac_record, permission_to_check, False)
            
            #logger.info(f"[RBAC] ===== PERMISSION CHECK DETAILS =====")
            #logger.info(f"[RBAC] User: {user_id} ({rbac_record.username})")
            #logger.info(f"[RBAC] Role: {rbac_record.role}")
            #logger.info(f"[RBAC] Endpoint: {endpoint_name}")
            #logger.info(f"[RBAC] Required Permission: {permission_to_check}")
            if permission_to_check == 'view_all_compliance_or_incident':
                logger.info(f"[RBAC] Composite Permission Check: view_all_compliance={rbac_record.view_all_compliance} OR view_all_incident={rbac_record.view_all_incident}")
            #logger.info(f"[RBAC] Permission Value: {has_permission}")
            #logger.info(f"[RBAC] Result: {'ACCESS GRANTED' if has_permission else 'ACCESS DENIED'}")
            #logger.info(f"[RBAC] =====================================")
            
            # Log all user permissions for debugging
            if not has_permission:
                logger.debug(f"[RBAC] User {user_id} all permissions:")
                #logger.debug(f"[RBAC] - Incident: create={rbac_record.create_incident}, edit={rbac_record.edit_incident}, view={rbac_record.view_all_incident}, assign={rbac_record.assign_incident}, evaluate={rbac_record.evaluate_assigned_incident}, escalate={rbac_record.escalate_to_risk}, analytics={rbac_record.incident_performance_analytics}")
                #logger.debug(f"[RBAC] - Policy: create={rbac_record.create_policy}, edit={rbac_record.edit_policy}, view={rbac_record.view_all_policy}, approve={rbac_record.approve_policy}, analytics={rbac_record.policy_performance_analytics}")
                #logger.debug(f"[RBAC] - Audit: assign={rbac_record.assign_audit}, conduct={rbac_record.conduct_audit}, review={rbac_record.review_audit}, view_reports={rbac_record.view_audit_reports}, analytics={rbac_record.audit_performance_analytics}")
                #logger.debug(f"[RBAC] - Risk: create={rbac_record.create_risk}, edit={rbac_record.edit_risk}, view={rbac_record.view_all_risk}, assign={rbac_record.assign_risk}, evaluate={rbac_record.evaluate_assigned_risk}, analytics={rbac_record.risk_performance_analytics}")
                #logger.debug(f"[RBAC] - Compliance: create={rbac_record.create_compliance}, edit={rbac_record.edit_compliance}, view={rbac_record.view_all_compliance}, approve={rbac_record.approve_compliance}, analytics={rbac_record.compliance_performance_analytics}")
            
            return {
                'allowed': has_permission,
                'user_id': user_id,
                'user_role': rbac_record.role,
                'user_username': rbac_record.username,
                'message': f'Permission {permission_to_check} {"granted" if has_permission else "denied"} for {endpoint_name}',
                'debug_info': {
                    'endpoint_name': endpoint_name,
                    'permission_checked': permission_to_check,
                    'user_role': rbac_record.role,
                    'user_active': rbac_record.is_active
                }
            }
            
        except Exception as e:
            logger.error(f"[RBAC] Error checking permission for {endpoint_name}: {e}")
            import traceback
            logger.error(f"[RBAC] Traceback: {traceback.format_exc()}")
            return {
                'allowed': False,
                'user_id': user_id if 'user_id' in locals() else None,
                'user_role': None,
                'user_username': None,
                'message': f'Error checking permission: {str(e)}',
                'debug_info': {'error': str(e)}
            }
    
    @staticmethod
    def has_incident_permission(user_id, permission_type):
        """
        Check if user has specific incident permission with detailed debugging
        permission_type: 'create', 'view', 'edit', 'assign', 'evaluate', 'escalate', 'analytics'
        """
        #print(f"[DEBUG RBAC] has_incident_permission called with user_id: {user_id}, permission_type: {permission_type}")
        try:
            #logger.debug(f"[RBAC] Checking incident permission: {permission_type} for user {user_id}")
            
            rbac_record = RBACUtils.get_user_rbac_record(user_id)
            #print(f"[DEBUG RBAC] get_user_rbac_record returned: {rbac_record}")
            if not rbac_record:
                logger.warning(f"[RBAC] Incident permission check failed - no RBAC record for user {user_id}")
                #print(f"[DEBUG RBAC] No RBAC record found, returning False")
                return False
            
            # Map permission types to model fields
            permission_field_map = {
                'create': 'create_incident',
                'view': 'view_all_incident',
                'edit': 'edit_incident',
                'assign': 'assign_incident',
                'evaluate': 'evaluate_assigned_incident',
                'escalate': 'escalate_to_risk',
                'analytics': 'incident_performance_analytics'
            }
            
            field_name = permission_field_map.get(permission_type)
            #print(f"[DEBUG RBAC] Mapped permission_type '{permission_type}' to field_name: {field_name}")
            if not field_name:
                logger.error(f"[RBAC] Invalid incident permission type: {permission_type}")
                #print(f"[DEBUG RBAC] Invalid permission type, returning False")
                return False
            
            has_permission = getattr(rbac_record, field_name, False)
            #print(f"[DEBUG RBAC] getattr(rbac_record, '{field_name}', False) returned: {has_permission}")
            
            #logger.info(f"[RBAC] User {user_id} ({rbac_record.role}) incident.{permission_type} = {'ALLOWED' if has_permission else 'DENIED'}")
            
            return has_permission
            
        except Exception as e:
            logger.error(f"[RBAC] Error checking incident permission {permission_type} for user {user_id}: {e}")
            #print(f"[DEBUG RBAC] Exception in has_incident_permission: {e}")
            return False
    
    @staticmethod
    def has_policy_permission(user_id, permission_type):
        """
        Check if user has specific policy permission with detailed debugging
        permission_type: 'create', 'view', 'edit', 'approve', 'create_framework', 'approve_framework', 'analytics'
        """
        try:
            #logger.debug(f"[RBAC] Checking policy permission: {permission_type} for user {user_id}")
            
            rbac_record = RBACUtils.get_user_rbac_record(user_id)
            if not rbac_record:
                logger.warning(f"[RBAC] Policy permission check failed - no RBAC record for user {user_id}")
                return False
            
            # Map permission types to model fields
            permission_field_map = {
                'create': 'create_policy',
                'view': 'view_all_policy',
                'edit': 'edit_policy',
                'approve': 'approve_policy',
                'create_framework': 'create_framework',
                'approve_framework': 'approve_framework',
                'analytics': 'policy_performance_analytics'
            }
            
            field_name = permission_field_map.get(permission_type)
            if not field_name:
                logger.error(f"[RBAC] Invalid policy permission type: {permission_type}")
                return False
            
            has_permission = getattr(rbac_record, field_name, False)
            
            #logger.info(f"[RBAC] User {user_id} ({rbac_record.role}) policy.{permission_type} = {'ALLOWED' if has_permission else 'DENIED'}")
            
            return has_permission
            
        except Exception as e:
            logger.error(f"[RBAC] Error checking policy permission {permission_type} for user {user_id}: {e}")
            return False
    
    @staticmethod
    def has_audit_permission(user_id, permission_type):
        """
        Check if user has specific audit permission with detailed debugging
        permission_type: 'assign', 'conduct', 'review', 'view_reports', 'analytics', 'view_all'
        """
        try:
            #logger.debug(f"[RBAC] Checking audit permission: {permission_type} for user {user_id}")
            
            rbac_record = RBACUtils.get_user_rbac_record(user_id)
            if not rbac_record:
                logger.warning(f"[RBAC] Audit permission check failed - no RBAC record for user {user_id}")
                return False
            
            # Map permission types to model fields
            permission_field_map = {
                'assign': 'assign_audit',
                'conduct': 'conduct_audit',
                'review': 'review_audit',
                'view_reports': 'view_audit_reports',
                'analytics': 'audit_performance_analytics',
                'view_all': 'assign_audit' # Changed from 'view_all_audits' to 'assign_audit'
            }
            
            field_name = permission_field_map.get(permission_type)
            if not field_name:
                logger.error(f"[RBAC] Invalid audit permission type: {permission_type}")
                return False
            
            has_permission = getattr(rbac_record, field_name, False)
            
            #logger.info(f"[RBAC] User {user_id} ({rbac_record.role}) audit.{permission_type} = {'ALLOWED' if has_permission else 'DENIED'}")
            
            return has_permission
            
        except Exception as e:
            logger.error(f"[RBAC] Error checking audit permission {permission_type} for user {user_id}: {e}")
            return False
    
    @staticmethod
    def has_risk_permission(user_id, permission_type):
        """
        Check if user has specific risk permission with detailed debugging
        permission_type: 'create', 'view', 'edit', 'approve', 'assign', 'evaluate', 'analytics'
        """
        try:
            #logger.debug(f"[RBAC] Checking risk permission: {permission_type} for user {user_id}")
            
            rbac_record = RBACUtils.get_user_rbac_record(user_id)
            if not rbac_record:
                logger.warning(f"[RBAC] Risk permission check failed - no RBAC record for user {user_id}")
                return False
            
            # Map permission types to model fields
            permission_field_map = {
                'create': 'create_risk',
                'view': 'view_all_risk',
                'edit': 'edit_risk',
                'approve': 'approve_risk',
                'assign': 'assign_risk',
                'evaluate': 'evaluate_assigned_risk',
                'analytics': 'risk_performance_analytics'
            }
            
            field_name = permission_field_map.get(permission_type)
            if not field_name:
                logger.error(f"[RBAC] Invalid risk permission type: {permission_type}")
                return False
            
            has_permission = getattr(rbac_record, field_name, False)
            
            #logger.info(f"[RBAC] User {user_id} ({rbac_record.role}) risk.{permission_type} = {'ALLOWED' if has_permission else 'DENIED'}")
            
            return has_permission
            
        except Exception as e:
            logger.error(f"[RBAC] Error checking risk permission {permission_type} for user {user_id}: {e}")
            return False
    
    @staticmethod
    def has_compliance_permission(user_id, permission_type):
        """
        Check if user has specific compliance permission with detailed debugging
        permission_type: 'CreateCompliance', 'EditCompliance', 'ApproveCompliance', 'ViewAllCompliance', 'CompliancePerformanceAnalytics'
        or legacy types: 'create', 'view', 'edit', 'approve', 'analytics'
        """
        try:
            #logger.debug(f"[RBAC] Checking compliance permission: {permission_type} for user {user_id}")
            
            rbac_record = RBACUtils.get_user_rbac_record(user_id)
            if not rbac_record:
                logger.warning(f"[RBAC] Compliance permission check failed - no RBAC record for user {user_id}")
                return False
            
            # Map permission types to model fields (5 main features + legacy support)
            permission_field_map = {
                # 5 Main Features (exact field names from RBAC table)
                'CreateCompliance': 'create_compliance',
                'EditCompliance': 'edit_compliance', 
                'ApproveCompliance': 'approve_compliance',
                'ViewAllCompliance': 'view_all_compliance',
                'CompliancePerformanceAnalytics': 'compliance_performance_analytics',
                
                # Legacy support (map to main features)
                'create': 'create_compliance',
                'view': 'view_all_compliance',
                'edit': 'edit_compliance',
                'approve': 'approve_compliance',
                'analytics': 'compliance_performance_analytics'
            }
            
            field_name = permission_field_map.get(permission_type)
            if not field_name:
                logger.error(f"[RBAC] Invalid compliance permission type: {permission_type}")
                return False
            
            has_permission = getattr(rbac_record, field_name, False)
            
            #logger.info(f"[RBAC] User {user_id} ({rbac_record.role}) compliance.{permission_type} = {'ALLOWED' if has_permission else 'DENIED'}")
            
            return has_permission
            
        except Exception as e:
            logger.error(f"[RBAC] Error checking compliance permission {permission_type} for user {user_id}: {e}")
            return False
    
    @staticmethod
    def log_user_login_permissions(user_id):
        """Log comprehensive permissions when user logs in with detailed debugging"""
        try:
            #logger.info(f"[RBAC] ===== USER LOGIN PERMISSIONS AUDIT =====")
            
            rbac_record = RBACUtils.get_user_rbac_record(user_id)
            if not rbac_record:
                logger.warning(f"[RBAC] No RBAC record found for user {user_id} during login")
                return
            
            #logger.info(f"[RBAC] User ID: {user_id}")
            #logger.info(f"[RBAC] Username: {rbac_record.username}")
            #logger.info(f"[RBAC] Role: {rbac_record.role}")
            #logger.info(f"[RBAC] Account Status: {'ACTIVE' if rbac_record.is_active == 'Y' else 'INACTIVE'}")
            #logger.info(f"[RBAC] Login Time: {timezone.now()}")
            #logger.info(f"[RBAC] ")
            
            #logger.info(f"[RBAC] === INCIDENT MODULE PERMISSIONS ===")
            #logger.info(f"[RBAC] Create Incidents: {'YES' if rbac_record.create_incident else 'NO'}")
            #logger.info(f"[RBAC] View All Incidents: {'YES' if rbac_record.view_all_incident else 'NO'}")
            #logger.info(f"[RBAC] Edit Incidents: {'YES' if rbac_record.edit_incident else 'NO'}")
            #logger.info(f"[RBAC] Assign Incidents: {'YES' if rbac_record.assign_incident else 'NO'}")
            #logger.info(f"[RBAC] Evaluate Assigned Incidents: {'YES' if rbac_record.evaluate_assigned_incident else 'NO'}")
            #logger.info(f"[RBAC] Escalate to Risk: {'YES' if rbac_record.escalate_to_risk else 'NO'}")
            #logger.info(f"[RBAC] Incident Analytics: {'YES' if rbac_record.incident_performance_analytics else 'NO'}")
            
            #logger.info(f"[RBAC] === POLICY MODULE PERMISSIONS ===")
            #logger.info(f"[RBAC] Create Policy: {'YES' if rbac_record.create_policy else 'NO'}")
            #logger.info(f"[RBAC] View All Policy: {'YES' if rbac_record.view_all_policy else 'NO'}")
            #logger.info(f"[RBAC] Edit Policy: {'YES' if rbac_record.edit_policy else 'NO'}")
            #logger.info(f"[RBAC] Approve Policy: {'YES' if rbac_record.approve_policy else 'NO'}")
            #logger.info(f"[RBAC] Create Framework: {'YES' if rbac_record.create_framework else 'NO'}")
            #logger.info(f"[RBAC] Approve Framework: {'YES' if rbac_record.approve_framework else 'NO'}")
            #logger.info(f"[RBAC] Policy Analytics: {'YES' if rbac_record.policy_performance_analytics else 'NO'}")
            
            #logger.info(f"[RBAC] === AUDIT MODULE PERMISSIONS ===")
            #logger.info(f"[RBAC] Assign Audit: {'YES' if rbac_record.assign_audit else 'NO'}")
            #logger.info(f"[RBAC] Conduct Audit: {'YES' if rbac_record.conduct_audit else 'NO'}")
            #logger.info(f"[RBAC] Review Audit: {'YES' if rbac_record.review_audit else 'NO'}")
            #logger.info(f"[RBAC] View Audit Reports: {'YES' if rbac_record.view_audit_reports else 'NO'}")
            #logger.info(f"[RBAC] View All Audits: {'YES' if rbac_record.assign_audit else 'NO'}") # Changed from 'view_all_audits' to 'assign_audit'
            #logger.info(f"[RBAC] Audit Analytics: {'YES' if rbac_record.audit_performance_analytics else 'NO'}")
            
            #logger.info(f"[RBAC] === RISK MODULE PERMISSIONS ===")
            #logger.info(f"[RBAC] Create Risk: {'YES' if rbac_record.create_risk else 'NO'}")
            #logger.info(f"[RBAC] View All Risk: {'YES' if rbac_record.view_all_risk else 'NO'}")
            #logger.info(f"[RBAC] Edit Risk: {'YES' if rbac_record.edit_risk else 'NO'}")
            #logger.info(f"[RBAC] Approve Risk: {'YES' if rbac_record.approve_risk else 'NO'}")
            #logger.info(f"[RBAC] Assign Risk: {'YES' if rbac_record.assign_risk else 'NO'}")
            #logger.info(f"[RBAC] Evaluate Assigned Risk: {'YES' if rbac_record.evaluate_assigned_risk else 'NO'}")
            #logger.info(f"[RBAC] Risk Analytics: {'YES' if rbac_record.risk_performance_analytics else 'NO'}")
            
            #logger.info(f"[RBAC] === COMPLIANCE MODULE PERMISSIONS ===")
            #logger.info(f"[RBAC] Create Compliance: {'YES' if rbac_record.create_compliance else 'NO'}")
            #logger.info(f"[RBAC] View All Compliance: {'YES' if rbac_record.view_all_compliance else 'NO'}")
            #logger.info(f"[RBAC] Edit Compliance: {'YES' if rbac_record.edit_compliance else 'NO'}")
            #logger.info(f"[RBAC] Approve Compliance: {'YES' if rbac_record.approve_compliance else 'NO'}")
            #logger.info(f"[RBAC] Compliance Analytics: {'YES' if rbac_record.compliance_performance_analytics else 'NO'}")
            
            #logger.info(f"[RBAC] ===============================================")
            
        except Exception as e:
            logger.error(f"[RBAC] Error logging permissions for user {user_id}: {e}")
    
    @staticmethod
    def get_user_permissions_summary(user_id):
        """Get a comprehensive summary of all permissions for a user"""
        try:
            rbac_record = RBACUtils.get_user_rbac_record(user_id)
            if not rbac_record:
                return None
            
            return {
                'user_id': user_id,
                'username': rbac_record.username,
                'role': rbac_record.role,
                'is_active': rbac_record.is_active == 'Y',
                'permissions': {
                    'incident': {
                        'has_access': rbac_record.has_incident_access(),
                        'create': rbac_record.create_incident,
                        'view_all': rbac_record.view_all_incident,
                        'edit': rbac_record.edit_incident,
                        'assign': rbac_record.assign_incident,
                        'evaluate': rbac_record.evaluate_assigned_incident,
                        'escalate': rbac_record.escalate_to_risk,
                        'analytics': rbac_record.incident_performance_analytics,
                    },
                    'policy': {
                        'has_access': rbac_record.has_policy_access(),
                        'create': rbac_record.create_policy,
                        'view_all': rbac_record.view_all_policy,
                        'edit': rbac_record.edit_policy,
                        'approve': rbac_record.approve_policy,
                        'create_framework': rbac_record.create_framework,
                        'approve_framework': rbac_record.approve_framework,
                        'analytics': rbac_record.policy_performance_analytics,
                    },
                    'audit': {
                        'has_access': rbac_record.has_audit_access(),
                        'assign': rbac_record.assign_audit,
                        'conduct': rbac_record.conduct_audit,
                        'review': rbac_record.review_audit,
                        'view_reports': rbac_record.view_audit_reports,
                        'analytics': rbac_record.audit_performance_analytics,
                    },
                    'risk': {
                        'has_access': rbac_record.has_risk_access(),
                        'create': rbac_record.create_risk,
                        'view_all': rbac_record.view_all_risk,
                        'edit': rbac_record.edit_risk,
                        'approve': rbac_record.approve_risk,
                        'assign': rbac_record.assign_risk,
                        'evaluate': rbac_record.evaluate_assigned_risk,
                        'analytics': rbac_record.risk_performance_analytics,
                    },
                    'compliance': {
                        'has_access': rbac_record.has_compliance_access(),
                        'create': rbac_record.create_compliance,
                        'view_all': rbac_record.view_all_compliance,
                        'edit': rbac_record.edit_compliance,
                        'approve': rbac_record.approve_compliance,
                        'analytics': rbac_record.compliance_performance_analytics,
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"[RBAC] Error getting permissions summary: {e}")
            return None
    
    @staticmethod
    def has_permission(user_id, module, permission_type):
        """
        Generic permission checker that routes to specific module permission methods
        
        Args:
            user_id: User ID to check permissions for
            module: Module name ('incident', 'policy', 'audit', 'risk', 'compliance')
            permission_type: Permission type ('create', 'view', 'edit', 'approve', etc.)
        
        Returns:
            bool: True if user has permission, False otherwise
        """
        try:
            module = module.lower()
            
            if module == 'incident':
                return RBACUtils.has_incident_permission(user_id, permission_type)
            elif module == 'policy':
                return RBACUtils.has_policy_permission(user_id, permission_type)
            elif module == 'audit':
                return RBACUtils.has_audit_permission(user_id, permission_type)
            elif module == 'risk':
                return RBACUtils.has_risk_permission(user_id, permission_type)
            elif module == 'compliance':
                return RBACUtils.has_compliance_permission(user_id, permission_type)
            else:
                logger.error(f"[RBAC] Unknown module: {module}")
                return False
                
        except Exception as e:
            logger.error(f"[RBAC] Error in generic permission check: {e}")
            return False

    @staticmethod
    def debug_permission_check(user_id, action, resource_type, resource_id=None):
        """Debug function to log detailed permission checks"""
        try:
            #logger.info(f"[RBAC DEBUG] ===== DETAILED PERMISSION CHECK =====")
            #logger.info(f"[RBAC DEBUG] User ID: {user_id}")
            #logger.info(f"[RBAC DEBUG] Action: {action}")
            #logger.info(f"[RBAC DEBUG] Resource: {resource_type} (ID: {resource_id})")
            #logger.info(f"[RBAC DEBUG] Timestamp: {timezone.now()}")
            
            rbac_record = RBACUtils.get_user_rbac_record(user_id)
            if not rbac_record:
                logger.warning(f"[RBAC DEBUG] No RBAC record found for user {user_id}")
                return False
            
            #logger.info(f"[RBAC DEBUG] User Role: {rbac_record.role}")
            #logger.info(f"[RBAC DEBUG] User Active: {rbac_record.is_active}")
            
            # Module-specific permission checking
            if resource_type.lower() == 'incident':
                permissions = {
                    'CREATE_INCIDENT': rbac_record.create_incident,
                    'VIEW_INCIDENT': rbac_record.view_all_incident,
                    'EDIT_INCIDENT': rbac_record.edit_incident,
                    'ASSIGN_INCIDENT': rbac_record.assign_incident,
                    'EVALUATE_INCIDENT': rbac_record.evaluate_assigned_incident,
                    'ESCALATE_INCIDENT': rbac_record.escalate_to_risk,
                    'INCIDENT_ANALYTICS': rbac_record.incident_performance_analytics,
                }
                
                #logger.info(f"[RBAC DEBUG] Incident Permissions: {permissions}")
                
                # Determine if action is allowed
                action_permission_map = {
                    'CREATE_INCIDENT': 'create_incident',
                    'VIEW_INCIDENT_DETAILS': 'view_all_incident',
                    'LIST_INCIDENTS': 'view_all_incident',
                    'EDIT_INCIDENT': 'edit_incident',
                    'UPDATE_INCIDENT_STATUS': 'edit_incident',
                    'ASSIGN_INCIDENT': 'assign_incident',
                    'ESCALATE_INCIDENT': 'escalate_to_risk',
                    'INCIDENT_DASHBOARD': 'view_all_incident',
                    'INCIDENT_ANALYTICS': 'incident_performance_analytics',
                    'EXPORT_INCIDENTS': 'view_all_incident',
                }
                
                required_permission = action_permission_map.get(action)
                if required_permission:
                    has_permission = getattr(rbac_record, required_permission, False)
                    #logger.info(f"[RBAC DEBUG] Action '{action}' requires '{required_permission}': {'GRANTED' if has_permission else 'DENIED'}")
                    #logger.info(f"[RBAC DEBUG] ========================================")
                    return has_permission
            
            elif resource_type.lower() == 'policy':
                permissions = {
                    'CREATE_POLICY': rbac_record.create_policy,
                    'VIEW_POLICY': rbac_record.view_all_policy,
                    'EDIT_POLICY': rbac_record.edit_policy,
                    'APPROVE_POLICY': rbac_record.approve_policy,
                    'CREATE_FRAMEWORK': rbac_record.create_framework,
                    'APPROVE_FRAMEWORK': rbac_record.approve_framework,
                    'POLICY_ANALYTICS': rbac_record.policy_performance_analytics,
                }
                
                #logger.info(f"[RBAC DEBUG] Policy Permissions: {permissions}")
                
                # Determine if action is allowed
                action_permission_map = {
                    'POLICY_CREATE': 'create_policy',
                    'POLICY_VIEW': 'view_all_policy',
                    'POLICY_EDIT': 'edit_policy',
                    'POLICY_APPROVE': 'approve_policy',
                    'POLICY_ANALYTICS': 'policy_performance_analytics',
                }
                
                required_permission = action_permission_map.get(action)
                if required_permission:
                    has_permission = getattr(rbac_record, required_permission, False)
                    #logger.info(f"[RBAC DEBUG] Action '{action}' requires '{required_permission}': {'GRANTED' if has_permission else 'DENIED'}")
                    #logger.info(f"[RBAC DEBUG] ========================================")
                    return has_permission
            
            elif resource_type.lower() == 'risk':
                permissions = {
                    'CREATE_RISK': rbac_record.create_risk,
                    'VIEW_RISK': rbac_record.view_all_risk,
                    'EDIT_RISK': rbac_record.edit_risk,
                    'APPROVE_RISK': rbac_record.approve_risk,
                    'ASSIGN_RISK': rbac_record.assign_risk,
                    'EVALUATE_RISK': rbac_record.evaluate_assigned_risk,
                    'RISK_ANALYTICS': rbac_record.risk_performance_analytics,
                }
                
                #logger.info(f"[RBAC DEBUG] Risk Permissions: {permissions}")
                
                # Determine if action is allowed
                action_permission_map = {
                    'RISK_CREATE': 'create_risk',
                    'RISK_VIEW': 'view_all_risk',
                    'RISK_EDIT': 'edit_risk',
                    'RISK_APPROVE': 'approve_risk',
                    'RISK_ASSIGN': 'assign_risk',
                    'RISK_EVALUATE': 'evaluate_assigned_risk',
                    'RISK_ANALYTICS': 'risk_performance_analytics',
                }
                
                required_permission = action_permission_map.get(action)
                if required_permission:
                    has_permission = getattr(rbac_record, required_permission, False)
                    #logger.info(f"[RBAC DEBUG] Action '{action}' requires '{required_permission}': {'GRANTED' if has_permission else 'DENIED'}")
                    #logger.info(f"[RBAC DEBUG] ========================================")
                    return has_permission
            
            elif resource_type.lower() == 'compliance':
                permissions = {
                    'CREATE_COMPLIANCE': rbac_record.create_compliance,
                    'VIEW_COMPLIANCE': rbac_record.view_all_compliance,
                    'EDIT_COMPLIANCE': rbac_record.edit_compliance,
                    'APPROVE_COMPLIANCE': rbac_record.approve_compliance,
                    'COMPLIANCE_ANALYTICS': rbac_record.compliance_performance_analytics,
                }
                
                #logger.info(f"[RBAC DEBUG] Compliance Permissions: {permissions}")
                
                # Determine if action is allowed
                action_permission_map = {
                    'COMPLIANCE_CREATE': 'create_compliance',
                    'COMPLIANCE_VIEW': 'view_all_compliance',
                    'COMPLIANCE_EDIT': 'edit_compliance',
                    'COMPLIANCE_APPROVE': 'approve_compliance',
                    'COMPLIANCE_ANALYTICS': 'compliance_performance_analytics',
                    'COMPLIANCE_VIEW_REQUIRED': 'view_all_compliance',
                    'VIEW_ALL_COMPLIANCE': 'view_all_compliance',
                    'VIEWALLCOMPLIANCE': 'view_all_compliance',
                }
                
                required_permission = action_permission_map.get(action)
                if required_permission:
                    has_permission = getattr(rbac_record, required_permission, False)
                    #logger.info(f"[RBAC DEBUG] Action '{action}' requires '{required_permission}': {'GRANTED' if has_permission else 'DENIED'}")
                    #logger.info(f"[RBAC DEBUG] ========================================")
                    return has_permission
            
            #logger.info(f"[RBAC DEBUG] Permission Result: UNKNOWN ACTION")
            #logger.info(f"[RBAC DEBUG] ========================================")
            return False
            
        except Exception as e:
            logger.error(f"[RBAC DEBUG] Error in permission check: {e}")
            return False
    
    @staticmethod
    def has_user_view_permission(user_id):
        """
        Check if user has permission to view user information
        Currently mapped to view_all_risk permission until dedicated field is added
        """
        try:
            #logger.debug(f"[RBAC] Checking user view permission for user {user_id}")
            
            rbac_record = RBACUtils.get_user_rbac_record(user_id)
            if not rbac_record:
                logger.warning(f"[RBAC] User view permission check failed - no RBAC record for user {user_id}")
                return False
            
            # For now, use view_all_risk as proxy. In the future, add 'view_users' field to RBAC model
            # Or check if user has any viewing permissions
            has_permission = (rbac_record.view_all_risk or 
                            rbac_record.view_all_incident or 
                            rbac_record.view_all_policy or 
                            rbac_record.view_all_compliance or
                            rbac_record.view_audit_reports)
            
            #logger.info(f"[RBAC] User {user_id} ({rbac_record.role}) user.view = {'ALLOWED' if has_permission else 'DENIED'}")
            
            return has_permission
            
        except Exception as e:
            logger.error(f"[RBAC] Error checking user view permission for user {user_id}: {e}")
            return False
    
    @staticmethod
    def is_system_admin(user_id):
        """
        Check if user is a system administrator
        Based on role = 'GRC Administrator'
        """
        try:
            #logger.debug(f"[RBAC] Checking system admin status for user {user_id}")
            
            rbac_record = RBACUtils.get_user_rbac_record(user_id)
            if not rbac_record:
                logger.warning(f"[RBAC] System admin check failed - no RBAC record for user {user_id}")
                return False
            
            is_admin = (rbac_record.role == 'GRC Administrator')
            
            #logger.info(f"[RBAC] User {user_id} ({rbac_record.role}) system.admin = {'ALLOWED' if is_admin else 'DENIED'}")
            
            return is_admin
            
        except Exception as e:
            logger.error(f"[RBAC] Error checking system admin status for user {user_id}: {e}")
            return False
    
    @staticmethod
    def check_permission_by_constant(user_id, permission_constant):
        """
        Check permission using the permission constants defined in permissions.py
        This is used by the RBAC decorators
        """
        try:
            #logger.debug(f"[RBAC] Checking permission constant '{permission_constant}' for user {user_id}")
            
            # Import here to avoid circular imports
            from .permissions import (
                RISK_VIEW, RISK_CREATE, RISK_UPDATE, RISK_DELETE, RISK_ASSIGN, RISK_APPROVE, RISK_REVIEW, RISK_ANALYTICS,
                INCIDENT_VIEW, INCIDENT_CREATE, INCIDENT_UPDATE, INCIDENT_DELETE,
                COMPLIANCE_VIEW, USER_VIEW, SYSTEM_ADMIN,
                POLICY_VIEW, POLICY_CREATE, POLICY_UPDATE, POLICY_DELETE, POLICY_APPROVE, POLICY_ANALYTICS,
                AUDIT_VIEW, AUDIT_CONDUCT, AUDIT_REVIEW, AUDIT_ASSIGN, AUDIT_ANALYTICS
            )
            
            rbac_record = RBACUtils.get_user_rbac_record(user_id)
            if not rbac_record:
                logger.warning(f"[RBAC] Permission check failed - no RBAC record for user {user_id}")
                return False
            
            # Special handling for USER_VIEW and SYSTEM_ADMIN
            if permission_constant == USER_VIEW:
                return RBACUtils.has_user_view_permission(user_id)
            elif permission_constant == SYSTEM_ADMIN:
                return RBACUtils.is_system_admin(user_id)
            
            # For other permissions, check the field directly
            has_permission = getattr(rbac_record, permission_constant, False)
            
            #logger.info(f"[RBAC] User {user_id} permission '{permission_constant}' = {'ALLOWED' if has_permission else 'DENIED'}")
            
            return has_permission
            
        except Exception as e:
            logger.error(f"[RBAC] Error checking permission constant '{permission_constant}' for user {user_id}: {e}")
            return False

    @staticmethod
    def has_event_permission(user_id, permission_type):
        """
        Check if user has specific event permission
        
        Args:
            user_id: User ID to check
            permission_type: Type of event permission ('view_all', 'view_module', 'create', 'edit', 'approve', 'reject', 'archive', 'analytics')
        
        Returns:
            bool: True if user has permission, False otherwise
        """
        try:
            rbac_record = RBAC.objects.filter(user=user_id, is_active='Y').first()
            if not rbac_record:
                logger.warning(f"[RBAC EVENT] No RBAC record found for user {user_id}")
                return False
            
            # Check if user has admin roles that should have full event access
            admin_roles = [
                'GRC Administrator',
                'Audit Manager', 
                'Internal Auditor',
                'External Auditor',
                'Audit Reviewer'
            ]
            
            if rbac_record.role in admin_roles:
                #logger.info(f"[RBAC EVENT] User {user_id} has admin role '{rbac_record.role}' - granting full event access")
                return True
            
            # Map permission types to correct model fields
            permission_field_map = {
                'view_all': 'view_all_event',
                'view_module': 'view_module_event',
                'create': 'create_event',
                'edit': 'edit_event',
                'approve': 'approve_event',
                'reject': 'reject_event',
                'archive': 'archive_event',
                'analytics': 'event_performance_analytics'
            }
            
            permission_field = permission_field_map.get(permission_type)
            if not permission_field:
                logger.error(f"[RBAC EVENT] Invalid permission type: {permission_type}")
                return False
            
            has_permission = getattr(rbac_record, permission_field, False)
            
            #logger.info(f"[RBAC EVENT] User {user_id} event.{permission_type} = {'ALLOWED' if has_permission else 'DENIED'}")
            #logger.info(f"[RBAC EVENT] User Details - Role: {rbac_record.role}, Field Checked: {permission_field}")
            
            return has_permission
            
        except Exception as e:
            logger.error(f"[RBAC EVENT] Error checking {permission_type} permission for user {user_id}: {e}")
            return False

    @staticmethod
    def get_user_event_permissions(user_id):
        """
        Get all event permissions for a user
        
        Args:
            user_id: User ID to check
        
        Returns:
            dict: Dictionary of event permissions
        """
        try:
            rbac_record = RBAC.objects.filter(user=user_id, is_active='Y').first()
            if not rbac_record:
                logger.warning(f"[RBAC EVENT] No RBAC record found for user {user_id}")
                return {}
            
            # Check if user has admin roles that should have full event access
            admin_roles = [
                'GRC Administrator',
                'Audit Manager', 
                'Internal Auditor',
                'External Auditor',
                'Audit Reviewer'
            ]
            
            is_admin = rbac_record.role in admin_roles
            
            permissions = {
                'view_all_event': is_admin or rbac_record.view_all_event,
                'view_module_event': is_admin or rbac_record.view_module_event,
                'create_event': is_admin or rbac_record.create_event,
                'edit_event': is_admin or rbac_record.edit_event,
                'approve_event': is_admin or rbac_record.approve_event,
                'reject_event': is_admin or rbac_record.reject_event,
                'archive_event': is_admin or rbac_record.archive_event,
                'event_performance_analytics': is_admin or rbac_record.event_performance_analytics,
                'is_admin': is_admin,
                'role': rbac_record.role
            }
            
            #logger.info(f"[RBAC EVENT] User {user_id} event permissions: {permissions}")
            return permissions
            
        except Exception as e:
            logger.error(f"[RBAC EVENT] Error getting event permissions for user {user_id}: {e}")
            return {}

    @staticmethod
    def get_user_accessible_modules(user_id):
        """
        Get list of modules the user can access for event filtering
        
        Args:
            user_id: User ID to check
        
        Returns:
            list: List of accessible module names (as stored in events table)
        """
        try:
            rbac_record = RBAC.objects.filter(user=user_id, is_active='Y').first()
            if not rbac_record:
                logger.warning(f"[RBAC EVENT] No RBAC record found for user {user_id}")
                return []
            
            # Check if user has admin roles that should have access to all modules
            admin_roles = [
                'GRC Administrator',
                'Audit Manager', 
                'Internal Auditor',
                'External Auditor',
                'Audit Reviewer'
            ]
            
            if rbac_record.role in admin_roles:
                #logger.info(f"[RBAC EVENT] User {user_id} has admin role - granting access to all modules")
                # Return all possible module names as they appear in the events table
                return ['Compliance Management', 'Policy Management', 'Audit Management', 'Risk Management', 'Incident Management']
            
            # If user has view_all_event, they can see all modules
            if rbac_record.view_all_event:
                #logger.info(f"[RBAC EVENT] User {user_id} has view_all_event permission - granting access to all modules")
                return ['Compliance Management', 'Policy Management', 'Audit Management', 'Risk Management', 'Incident Management']
            
            # If user has view_module_event, determine which modules they can access based on their other permissions
            accessible_modules = []
            
            if rbac_record.view_module_event:
                # Check which modules the user has access to based on their other permissions
                # Map RBAC module access to actual module names in events table
                if rbac_record.has_compliance_access():
                    accessible_modules.append('Compliance Management')
                if rbac_record.has_policy_access():
                    accessible_modules.append('Policy Management')
                if rbac_record.has_audit_access():
                    accessible_modules.append('Audit Management')
                if rbac_record.has_risk_access():
                    accessible_modules.append('Risk Management')
                if rbac_record.has_incident_access():
                    accessible_modules.append('Incident Management')
            
            #logger.info(f"[RBAC EVENT] User {user_id} accessible modules: {accessible_modules}")
            return accessible_modules
            
        except Exception as e:
            logger.error(f"[RBAC EVENT] Error getting accessible modules for user {user_id}: {e}")
            return []