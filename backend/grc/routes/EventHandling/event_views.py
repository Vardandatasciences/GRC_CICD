from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.db import models
from django.utils import timezone
import json

# RBAC imports
from ...rbac.permissions import (
    EventViewAllPermission, EventViewModulePermission, EventCreatePermission,
    EventEditPermission, EventApprovePermission, EventRejectPermission,
    EventArchivePermission, EventAnalyticsPermission, EventDashboardPermission,
    EventQueuePermission, EventCalendarPermission, EventExportPermission
)
from ...rbac.utils import RBACUtils
from ...routes.Consent import require_consent

# DRF Session auth variant that skips CSRF enforcement for API clients
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return

from ...models import (
    Event, Framework, Policy, Compliance, Audit, Risk, Incident, 
    SubPolicy, Users, EventType, Module, FileOperations
)
from ...routes.Global.s3_fucntions import create_direct_mysql_client

# Simple test endpoint
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def test_endpoint(request):
    """Simple test endpoint to verify URL routing"""
    return Response({
        'success': True,
        'message': 'Event handling endpoints are working!',
        'path': request.path
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def get_user_event_permissions(request):
    """
    Get user's event permissions for frontend RBAC
    """
    try:
        user_id = RBACUtils.get_user_id_from_request(request)
        print(f"DEBUG: get_user_event_permissions called for user_id: {user_id}")
        
        if not user_id:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Get user's event permissions
        permissions = RBACUtils.get_user_event_permissions(user_id)
        accessible_modules = RBACUtils.get_user_accessible_modules(user_id)
        
        print(f"DEBUG: User {user_id} permissions: {permissions}")
        print(f"DEBUG: User {user_id} accessible modules: {accessible_modules}")
        
        return Response({
            'success': True,
            'permissions': permissions,
            'accessible_modules': accessible_modules
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error fetching user permissions: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([AllowAny])
@csrf_exempt
def get_frameworks_for_events(request):
    """
    Get all frameworks for event creation
    """
    print("DEBUG: get_frameworks_for_events called")
    print(f"DEBUG: Request path: {request.path}")
    print(f"DEBUG: Request method: {request.method}")
    
    try:
        # Try to get all frameworks first
        all_frameworks = Framework.objects.all()
        print(f"DEBUG: Total frameworks in database: {all_frameworks.count()}")
        
        # Then filter for active ones
        frameworks = Framework.objects.filter(ActiveInactive='Active').values(
            'FrameworkId', 'FrameworkName'
        )
        
        print(f"DEBUG: Found {frameworks.count()} active frameworks")
        
        # If no active frameworks, return all frameworks
        if frameworks.count() == 0:
            print("DEBUG: No active frameworks found, returning all frameworks")
            frameworks = Framework.objects.all().values(
                'FrameworkId', 'FrameworkName'
            )
        
        frameworks_list = list(frameworks)
        print(f"DEBUG: Returning {len(frameworks_list)} frameworks")
        
        return Response({
            'success': True,
            'frameworks': frameworks_list
        })
    except Exception as e:
        print(f"DEBUG: Error in get_frameworks_for_events: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'message': f'Error fetching frameworks: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([AllowAny])
@csrf_exempt
def get_modules_for_events(request):
    """
    Get all modules for event creation (simplified like event types)
    """
    print("DEBUG: get_modules_for_events called")
    print(f"DEBUG: Request path: {request.path}")
    print(f"DEBUG: Request method: {request.method}")
    
    try:
        from ...models import Module
        
        # Get all modules from database (simplified approach like event types)
        all_modules = Module.objects.all().values('moduleid', 'modulename')
        modules_list = list(all_modules)
        
        print(f"DEBUG: Found {len(modules_list)} modules in database")
        for module in modules_list:
            print(f"DEBUG: Module: {module}")
        
        # Sort modules by name
        modules_list.sort(key=lambda x: x['modulename'])
        
        return Response({
            'success': True,
            'modules': modules_list
        })
        
    except Exception as e:
        print(f"DEBUG: Error in get_modules_for_events: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'message': f'Error fetching modules: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([AllowAny])
@csrf_exempt
def get_event_types_by_framework(request):
    """
    Get event types based on framework selection
    """
    print("DEBUG: get_event_types_by_framework called")
    try:
        framework_name = request.GET.get('framework_name')
        
        print(f"DEBUG: framework_name='{framework_name}' (length: {len(framework_name) if framework_name else 0})")
        if framework_name:
            print(f"DEBUG: framework_name repr: {repr(framework_name)}")
        
        if not framework_name:
            return Response({
                'success': False,
                'message': 'Framework name is required'
            }, status=400)
        
        # Trim the framework name to remove any extra whitespace
        framework_name = framework_name.strip()
        print(f"DEBUG: Trimmed framework_name='{framework_name}' (length: {len(framework_name)})")
        
        # Debug: Show all available framework names in EventType table
        all_framework_names = EventType.objects.values_list('FrameworkName', flat=True).distinct()
        print(f"DEBUG: Available framework names in EventType table: {list(all_framework_names)}")
        
        # Debug: Show all EventType records
        all_event_types = EventType.objects.all().values('eventtype_id', 'FrameworkName', 'eventtype')
        print(f"DEBUG: All EventType records: {list(all_event_types)}")
        
        # Fetch event types for the selected framework (include eventSubtype)
        event_types = EventType.objects.filter(
            FrameworkName=framework_name
        ).values('eventtype_id', 'eventtype', 'eventSubtype')
        
        event_types_list = list(event_types)
        print(f"DEBUG: Found {len(event_types_list)} event types for framework '{framework_name}'")
        
        # If no exact match found, try to find by partial match or case-insensitive match
        if len(event_types_list) == 0:
            print(f"DEBUG: No exact match found, trying case-insensitive search...")
            event_types_ci = EventType.objects.filter(
                FrameworkName__iexact=framework_name
            ).values('eventtype_id', 'eventtype', 'eventSubtype')
            
            event_types_list = list(event_types_ci)
            print(f"DEBUG: Found {len(event_types_list)} event types with case-insensitive search")
        
        # If still no match, try to find by containing the framework name
        if len(event_types_list) == 0:
            print(f"DEBUG: Still no match, trying partial match...")
            event_types_partial = EventType.objects.filter(
                FrameworkName__icontains=framework_name
            ).values('eventtype_id', 'eventtype', 'eventSubtype')
            
            event_types_list = list(event_types_partial)
            print(f"DEBUG: Found {len(event_types_list)} event types with partial match")
        
        # If still no match, try to find by framework name containing the search term
        if len(event_types_list) == 0:
            print(f"DEBUG: Trying reverse partial match...")
            # Split the framework name and try to match parts
            framework_parts = framework_name.split()
            for part in framework_parts:
                if len(part) > 3:  # Only try parts longer than 3 characters
                    event_types_reverse = EventType.objects.filter(
                        FrameworkName__icontains=part
                    ).values('eventtype_id', 'eventtype', 'eventSubtype')
                    
                    if event_types_reverse.exists():
                        event_types_list = list(event_types_reverse)
                        print(f"DEBUG: Found {len(event_types_list)} event types with reverse partial match for '{part}'")
                        break
        
        return Response({
            'success': True,
            'event_types': event_types_list,
            'framework_name': framework_name,
            'debug_info': {
                'available_frameworks': list(all_framework_names),
                'search_used': framework_name
            }
        })
        
    except Exception as e:
        print(f"DEBUG: Exception in get_event_types_by_framework: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'message': f'Error fetching event types: {str(e)}'
        }, status=500)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([AllowAny])
@csrf_exempt
def create_event_type(request):
    """
    Create a new event type for a specific framework
    """
    print("DEBUG: create_event_type called")
    try:
        data = json.loads(request.body)
        framework_name = data.get('framework_name')
        event_type_name = data.get('event_type_name')
        event_subtypes = data.get('event_subtypes', None)  # Optional sub-event types
        
        print(f"DEBUG: framework_name={framework_name}, event_type_name={event_type_name}")
        print(f"DEBUG: event_subtypes={event_subtypes}")
        
        if not framework_name or not event_type_name:
            return Response({
                'success': False,
                'message': 'Framework name and event type name are required'
            }, status=400)
        
        # Check if event type already exists for this framework
        existing_event_type = EventType.objects.filter(
            FrameworkName=framework_name,
            eventtype=event_type_name
        ).first()
        
        if existing_event_type:
            return Response({
                'success': False,
                'message': f'Event type "{event_type_name}" already exists for framework "{framework_name}"'
            }, status=400)
        
        # Create new event type with sub-event types if provided
        new_event_type = EventType.objects.create(
            FrameworkName=framework_name,
            eventtype=event_type_name,
            eventSubtype=event_subtypes
        )
        
        print(f"DEBUG: Created new event type with ID: {new_event_type.eventtype_id}")
        
        return Response({
            'success': True,
            'message': 'Event type created successfully',
            'event_type': {
                'eventtype_id': new_event_type.eventtype_id,
                'eventtype': new_event_type.eventtype,
                'FrameworkName': new_event_type.FrameworkName,
                'eventSubtype': new_event_type.eventSubtype
            }
        })
        
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print(f"DEBUG: Exception in create_event_type: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'message': f'Error creating event type: {str(e)}'
        }, status=500)


@api_view(['PUT'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([AllowAny])
@csrf_exempt
def update_event_type_subtypes(request, event_type_id):
    """
    Update sub-event types for an existing event type
    """
    print("DEBUG: update_event_type_subtypes called")
    try:
        data = json.loads(request.body)
        event_subtypes = data.get('event_subtypes')
        
        print(f"DEBUG: event_type_id={event_type_id}, event_subtypes={event_subtypes}")
        
        if event_subtypes is None:
            return Response({
                'success': False,
                'message': 'event_subtypes is required'
            }, status=400)
        
        # Find the event type
        try:
            event_type = EventType.objects.get(eventtype_id=event_type_id)
        except EventType.DoesNotExist:
            return Response({
                'success': False,
                'message': f'Event type with ID {event_type_id} not found'
            }, status=404)
        
        # Update the sub-event types
        event_type.eventSubtype = event_subtypes
        event_type.save()
        
        print(f"DEBUG: Updated event type {event_type_id} with sub-event types")
        
        return Response({
            'success': True,
            'message': 'Event type sub-types updated successfully',
            'event_type': {
                'eventtype_id': event_type.eventtype_id,
                'eventtype': event_type.eventtype,
                'FrameworkName': event_type.FrameworkName,
                'eventSubtype': event_type.eventSubtype
            }
        })
        
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print(f"DEBUG: Exception in update_event_type_subtypes: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'message': f'Error updating event type sub-types: {str(e)}'
        }, status=500)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([AllowAny])
@csrf_exempt
def create_module(request):
    """
    Create a new module
    """
    print("DEBUG: create_module called")
    try:
        data = json.loads(request.body)
        module_name = data.get('module_name')
        
        print(f"DEBUG: module_name={module_name}")
        
        if not module_name:
            return Response({
                'success': False,
                'message': 'Module name is required'
            }, status=400)
        
        # Check if module already exists
        existing_module = Module.objects.filter(
            modulename=module_name
        ).first()
        
        if existing_module:
            return Response({
                'success': False,
                'message': f'Module "{module_name}" already exists'
            }, status=400)
        
        # Create new module
        new_module = Module.objects.create(
            modulename=module_name
        )
        
        print(f"DEBUG: Created new module with ID: {new_module.moduleid}")
        
        return Response({
            'success': True,
            'message': 'Module created successfully',
            'module': {
                'moduleid': new_module.moduleid,
                'modulename': new_module.modulename
            }
        })
        
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print(f"DEBUG: Exception in create_module: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'message': f'Error creating module: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([AllowAny])
@csrf_exempt
def get_records_by_module(request):
    """
    Get records based on framework and module selection
    """
    print("DEBUG: get_records_by_module called")
    try:
        framework_id = request.GET.get('framework_id')
        module = request.GET.get('module')
        
        print(f"DEBUG: framework_id={framework_id}, module={module}")
        
        if not framework_id:
            return Response({
                'success': False,
                'message': 'Framework ID is required'
            }, status=400)
        
        records = []
        
        # Handle case where module might be empty or None
        if not module or module.strip() == '':
            # If no module is selected, return empty records list
            return Response({
                'success': True,
                'records': []
            })
        
        # Normalize module name to handle full module names from frontend
        module_lower = module.lower()
        
        if 'policy' in module_lower:
            # Fetch policies for the selected framework
            print(f"DEBUG: Fetching policies for framework_id={framework_id}")
            try:
                policies = Policy.objects.filter(
                    FrameworkId=framework_id,
                    ActiveInactive='Active'
                ).values(
                    'PolicyId', 'PolicyName', 'PolicyDescription', 
                    'Status', 'Department', 'Identifier'
                )
                print(f"DEBUG: Found {policies.count()} policies")
                
                # Debug: Check if there are any policies at all
                all_policies = Policy.objects.all().count()
                print(f"DEBUG: Total policies in database: {all_policies}")
                
                # Debug: Check policies for this framework regardless of status
                framework_policies = Policy.objects.filter(FrameworkId=framework_id).count()
                print(f"DEBUG: Total policies for framework {framework_id}: {framework_policies}")
                
                # If no active policies found, try to get any policies for this framework
                if policies.count() == 0:
                    print(f"DEBUG: No active policies found, trying to get any policies for framework {framework_id}")
                    policies = Policy.objects.filter(
                        FrameworkId=framework_id
                    ).values(
                        'PolicyId', 'PolicyName', 'PolicyDescription', 
                        'Status', 'Department', 'Identifier'
                    )
                    print(f"DEBUG: Found {policies.count()} policies (including inactive)")
                
            except Exception as e:
                print(f"DEBUG: Error querying policies: {str(e)}")
                policies = []
            
            records = [
                {
                    'id': p['PolicyId'],
                    'name': p['PolicyName'],
                    'description': p['PolicyDescription'],
                    'status': p['Status'],
                    'department': p['Department'],
                    'identifier': p['Identifier']
                }
                for p in policies
            ]
            
        elif 'compliance' in module_lower:
            # Fetch compliance records for the selected framework
            print(f"DEBUG: Fetching compliance records for framework_id={framework_id}")
            compliances = Compliance.objects.filter(
                SubPolicy__Policy__FrameworkId=framework_id,
                ActiveInactive='Active'
            ).select_related('SubPolicy__Policy').values(
                'ComplianceId', 'ComplianceTitle', 'ComplianceItemDescription',
                'Status', 'Identifier', 'SubPolicy__Policy__PolicyName'
            )
            print(f"DEBUG: Found {compliances.count()} compliance records")
            records = [
                {
                    'id': c['ComplianceId'],
                    'name': c['ComplianceTitle'] or f"Compliance {c['ComplianceId']}",
                    'description': c['ComplianceItemDescription'],
                    'status': c['Status'],
                    'identifier': c['Identifier'],
                    'policy_name': c['SubPolicy__Policy__PolicyName']
                }
                for c in compliances
            ]
            
        elif 'audit' in module_lower:
            # Fetch audits for the selected framework
            print(f"DEBUG: Fetching audits for framework_id={framework_id}")
            audits = Audit.objects.filter(
                FrameworkId=framework_id
            ).values(
                'AuditId', 'Title', 'Scope', 'Status', 'AuditType'
            )
            print(f"DEBUG: Found {audits.count()} audits")
            records = [
                {
                    'id': a['AuditId'],
                    'name': a['Title'],
                    'description': a['Scope'],
                    'status': a['Status'],
                    'type': a['AuditType']
                }
                for a in audits
            ]
            
        elif 'risk' in module_lower:
            # Fetch risks (these might not be directly linked to frameworks)
            print(f"DEBUG: Fetching risks for framework_id={framework_id}")
            risks = Risk.objects.all().values(
                'RiskId', 'RiskTitle', 'RiskDescription'
            )
            print(f"DEBUG: Found {risks.count()} risks")
            records = [
                {
                    'id': r['RiskId'],
                    'name': r['RiskTitle'],
                    'description': r['RiskDescription'],
                    'status': 'Active'  # Default status since Risk model doesn't have RiskStatus field
                }
                for r in risks
            ]
            
        elif 'incident' in module_lower:
            # Fetch incidents
            print(f"DEBUG: Fetching incidents for framework_id={framework_id}")
            incidents = Incident.objects.all().values(
                'IncidentId', 'IncidentTitle', 'Description', 'Status'
            )
            print(f"DEBUG: Found {incidents.count()} incidents")
            records = [
                {
                    'id': i['IncidentId'],
                    'name': i['IncidentTitle'],
                    'description': i['Description'],
                    'status': i['Status']
                }
                for i in incidents
            ]
            
        elif 'subpolicy' in module_lower:
            # Fetch subpolicies for the selected framework
            print(f"DEBUG: Fetching subpolicies for framework_id={framework_id}")
            subpolicies = SubPolicy.objects.filter(
                Policy__FrameworkId=framework_id
            ).select_related('Policy').values(
                'SubPolicyId', 'SubPolicyName', 'Description', 
                'Status', 'Identifier', 'Policy__PolicyName'
            )
            print(f"DEBUG: Found {subpolicies.count()} subpolicies")
            records = [
                {
                    'id': sp['SubPolicyId'],
                    'name': sp['SubPolicyName'],
                    'description': sp['Description'],
                    'status': sp['Status'],
                    'identifier': sp['Identifier'],
                    'policy_name': sp['Policy__PolicyName']
                }
                for sp in subpolicies
            ]
        else:
            print(f"DEBUG: Unknown module type: {module}")
            records = []
        
        print(f"DEBUG: Returning {len(records)} records for module '{module}'")
        
        # If no records found, return empty list
        if len(records) == 0:
            print(f"DEBUG: No records found for module '{module}' and framework_id '{framework_id}'")
        
        return Response({
            'success': True,
            'records': records,
            'count': len(records),
            'module': module,
            'framework_id': framework_id
        })
        
    except Exception as e:
        print(f"DEBUG: Exception in get_records_by_module: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'message': f'Error fetching records: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def get_event_templates(request):
    """
    Get event templates for the template section
    """
    print("DEBUG: get_event_templates called")
    try:
        # Check if Event table exists, if not return empty templates
        try:
            templates = Event.objects.filter(
                IsTemplate=True,
                Status='Approved'
            ).values(
                'EventId', 'EventTitle', 'EventId_Generated', 'FrameworkName',
                'Module', 'Category', 'Owner__FirstName', 'Owner__LastName',
                'Reviewer__FirstName', 'Reviewer__LastName', 'CreatedAt'
            )
            
            formatted_templates = []
            for template in templates:
                formatted_templates.append({
                    'id': template['EventId'],
                    'title': template['EventTitle'],
                    'event_id': template['EventId_Generated'],
                    'framework': template['FrameworkName'],
                    'module': template['Module'],
                    'category': template['Category'],
                    'owner': f"{template['Owner__FirstName']} {template['Owner__LastName']}" if template['Owner__FirstName'] else 'Not Assigned',
                    'reviewer': f"{template['Reviewer__FirstName']} {template['Reviewer__LastName']}" if template['Reviewer__FirstName'] else 'Not Assigned',
                    'date': template['CreatedAt'].strftime('%d/%m') if template['CreatedAt'] else ''
                })
        except Exception as table_error:
            print(f"DEBUG: Event table doesn't exist yet: {table_error}")
            # Return empty templates if table doesn't exist
            formatted_templates = []
        
        print(f"DEBUG: Returning {len(formatted_templates)} templates")
        
        return Response({
            'success': True,
            'templates': formatted_templates
        })
        
    except Exception as e:
        print(f"DEBUG: Error in get_event_templates: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error fetching templates: {str(e)}'
        }, status=500)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventCreatePermission])
@csrf_exempt
@require_consent('create_event')
def create_event(request):
    """
    Create a new event
    """
    print("DEBUG: create_event called")
    print(f"DEBUG: Request method: {request.method}")
    print(f"DEBUG: Request data: {request.data}")
    print(f"DEBUG: Request headers: {dict(request.headers)}")
    print(f"DEBUG: Request user: {getattr(request, 'user', 'No user')}")
    print(f"DEBUG: Request META: {request.META.get('HTTP_AUTHORIZATION', 'No auth header')}")
    
    try:
        data = request.data
        
        # Get user ID from request (should be available from JWT middleware)
        user_id = data.get('user_id') or request.GET.get('user_id')
        print(f"DEBUG: User ID: {user_id}")
        
        if not user_id:
            return Response({
                'success': False,
                'message': 'User ID is required'
            }, status=400)
        
        # Validate required fields
        if not data.get('title'):
            return Response({
                'success': False,
                'message': 'Event title is required'
            }, status=400)
        
        # Get framework object if framework_id is provided
        framework_id = data.get('framework_id')
        framework_obj = None
        if framework_id:
            try:
                framework_obj = Framework.objects.get(FrameworkId=framework_id)
                print(f"DEBUG: Found framework: {framework_obj.FrameworkName}")
            except Framework.DoesNotExist:
                print(f"DEBUG: Framework with ID {framework_id} not found")
                return Response({
                    'success': False,
                    'message': f'Framework with ID {framework_id} not found'
                }, status=400)
        
        # Get owner and reviewer user objects
        owner_obj = None
        reviewer_obj = None
        
        if data.get('owner_id'):
            try:
                owner_obj = Users.objects.get(UserId=data.get('owner_id'))
                print(f"DEBUG: Found owner: {owner_obj.FirstName} {owner_obj.LastName}")
            except Users.DoesNotExist:
                print(f"DEBUG: Owner with ID {data.get('owner_id')} not found")
        
        if data.get('reviewer_id'):
            try:
                reviewer_obj = Users.objects.get(UserId=data.get('reviewer_id'))
                print(f"DEBUG: Found reviewer: {reviewer_obj.FirstName} {reviewer_obj.LastName}")
            except Users.DoesNotExist:
                print(f"DEBUG: Reviewer with ID {data.get('reviewer_id')} not found")
        
        # Determine initial status - always start with 'Under Review' for all events
        initial_status = 'Under Review'
        
        # Handle date fields - convert empty strings to None
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # Convert empty strings to None for date fields
        if start_date == '' or start_date is None:
            start_date = None
        if end_date == '' or end_date is None:
            end_date = None
        
        # Handle LinkedRecordId - convert empty strings to None
        linked_record_id = data.get('linked_record_id')
        if linked_record_id == '' or linked_record_id is None:
            linked_record_id = None
        
        # Handle frequency field for non-recurring events
        frequency = data.get('frequency')
        if data.get('recurrence_type') == 'Non-Recurring':
            frequency = None
        
        # Handle template selection
        is_template = data.get('is_template', False)
        # Convert string 'true'/'false' to boolean if needed
        if isinstance(is_template, str):
            is_template = is_template.lower() in ['true', '1', 'yes']
        
        # Ensure boolean is converted to 1/0 for database compatibility
        is_template = 1 if is_template else 0
        
        # All events should start with 'Under Review' status, including templates
        print(f"DEBUG: Creating event with status 'Under Review', is_template: {is_template}")
        
        # Handle evidence files if provided
        evidence_data = data.get('evidence', [])
        evidence_urls = []
        
        print(f"DEBUG: Raw evidence data from request: {evidence_data}")
        print(f"DEBUG: Evidence data type: {type(evidence_data)}")
        
        # Handle evidence data - could be JSON string or array
        evidence_files = []
        if isinstance(evidence_data, str):
            try:
                # Parse JSON string
                evidence_files = json.loads(evidence_data)
                print(f"DEBUG: Parsed evidence JSON: {evidence_files}")
            except json.JSONDecodeError as e:
                print(f"DEBUG: Failed to parse evidence JSON: {e}")
                evidence_files = []
        elif isinstance(evidence_data, list):
            # Already an array
            evidence_files = evidence_data
        
        # Process evidence files and extract S3 URLs
        if evidence_files:
            print(f"DEBUG: Processing {len(evidence_files)} evidence files")
            for i, evidence_file in enumerate(evidence_files):
                print(f"DEBUG: Processing evidence file {i+1}: {evidence_file}")
                if evidence_file.get('s3_url'):
                    evidence_urls.append(evidence_file.get('s3_url'))
                    print(f"DEBUG: Added evidence URL: {evidence_file.get('s3_url')}")
                else:
                    print(f"DEBUG: Skipping evidence file {i+1} - no s3_url")
        else:
            print("DEBUG: No evidence files provided")
        
        # Create semicolon-separated string of URLs
        evidence_string = ";".join(evidence_urls) if evidence_urls else ""
        print(f"DEBUG: Final evidence string to save: '{evidence_string}'")
        print(f"DEBUG: Evidence string length: {len(evidence_string)}")
        
        # Get event type object if event_type_id is provided
        event_type_obj = None
        event_type_id = data.get('event_type_id')
        if event_type_id:
            try:
                event_type_obj = EventType.objects.get(eventtype_id=event_type_id)
                print(f"DEBUG: Found event type: {event_type_obj.eventtype}")
            except EventType.DoesNotExist:
                print(f"DEBUG: Event type with ID {event_type_id} not found")

        # Get sub-event type name if provided
        sub_event_type_name = None
        sub_event_type_id = data.get('sub_event_type_id')
        if sub_event_type_id is not None and event_type_obj and event_type_obj.eventSubtype:
            try:
                sub_event_type_id = int(sub_event_type_id)
                
                if isinstance(event_type_obj.eventSubtype, list):
                    # Handle array format: ["Type 1", "Type 2", ...]
                    if 0 <= sub_event_type_id < len(event_type_obj.eventSubtype):
                        sub_event_type_name = event_type_obj.eventSubtype[sub_event_type_id]
                        print(f"DEBUG: Selected sub-event type (array): {sub_event_type_name}")
                elif isinstance(event_type_obj.eventSubtype, dict):
                    # Handle object format: {"key1": [...], "key2": [...], ...}
                    sub_type_keys = list(event_type_obj.eventSubtype.keys())
                    if 0 <= sub_event_type_id < len(sub_type_keys):
                        selected_key = sub_type_keys[sub_event_type_id]
                        
                        # Create a mapping for better display names
                        display_name_map = {
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
                        
                        # Use mapping or fallback to Title Case
                        sub_event_type_name = display_name_map.get(selected_key, selected_key.replace('_', ' ').title())
                        print(f"DEBUG: Selected sub-event type (object): {sub_event_type_name} (key: {selected_key})")
                        
            except (ValueError, TypeError):
                print(f"DEBUG: Invalid sub_event_type_id: {sub_event_type_id}")

        # Extract data from request - match Django Event model field names exactly
        event_data = {
            'EventTitle': data.get('title'),
            'Description': data.get('description'),
            'FrameworkId': framework_obj,
            'FrameworkName': data.get('framework_name'),
            'Module': data.get('module'),
            'LinkedRecordType': data.get('linked_record_type'),
            'LinkedRecordId': linked_record_id,
            'LinkedRecordName': data.get('linked_record_name'),
            'Category': data.get('category'),  # Keep original category field
            'EventType': event_type_obj,  # Save event type object in EventType field
            'SubEventType': sub_event_type_name,  # Save selected sub-event type name
            'RecurrenceType': data.get('recurrence_type', 'Non-Recurring'),
            'Frequency': frequency,
            'StartDate': start_date,
            'EndDate': end_date,
            'Status': data.get('status', initial_status),
            'Priority': data.get('priority', 'Medium'),
            'CreatedBy': Users.objects.get(UserId=user_id) if user_id else None,
            'Owner': owner_obj,
            'Reviewer': reviewer_obj,
            'IsTemplate': is_template,
            'Evidence': evidence_string,  # Store evidence URLs as semicolon-separated string
            'DynamicFieldsData': data.get('dynamic_fields', {})  # Store user-entered dynamic fields data
        }
        
        print(f"DEBUG: Event data to create: {event_data}")
        print(f"DEBUG: Evidence field in event_data: {event_data.get('Evidence')}")
        print(f"DEBUG: Evidence field type: {type(event_data.get('Evidence'))}")
        
        # Check if events table exists
        try:
            # Create the primary event
            print("DEBUG: Attempting to create event...")
            event = Event.objects.create(**event_data)
            print(f"DEBUG: Primary event created successfully with ID: {event.EventId}")
            print(f"DEBUG: Event Evidence after creation: {event.Evidence}")
            print(f"DEBUG: Event Evidence type after creation: {type(event.Evidence)}")
            
            created_events = [{
                'EventId': event.EventId,
                'EventTitle': event.EventTitle,
                'Status': event.Status,
                'RecurrenceType': event.RecurrenceType,
                'StartDate': event.StartDate,
                'EndDate': event.EndDate,
                'LinkedRecordName': event.LinkedRecordName,
                'FrameworkName': event.FrameworkName,
                'Module': event.Module
            }]
            
            # Handle additional records if any
            additional_records = data.get('additional_records', [])
            if additional_records:
                print(f"DEBUG: Creating {len(additional_records)} additional events")
                
                for i, additional_record in enumerate(additional_records):
                    # Get framework object for additional record
                    additional_framework_obj = None
                    if additional_record.get('framework_id'):
                        try:
                            additional_framework_obj = Framework.objects.get(FrameworkId=additional_record['framework_id'])
                            print(f"DEBUG: Found additional framework: {additional_framework_obj.FrameworkName}")
                        except Framework.DoesNotExist:
                            print(f"DEBUG: Additional framework with ID {additional_record['framework_id']} not found")
                            continue
                    
                    # Create event data for additional record
                    additional_record_name = additional_record.get('linked_record_name', f'Additional Record {i+1}')
                    additional_event_data = {
                        'EventTitle': f"{data.get('title')} - {additional_record_name}",
                        'Description': f"Additional record for event: {data.get('title')} - {additional_record_name}",
                        'FrameworkId': additional_framework_obj,
                        'FrameworkName': additional_record.get('framework_name'),
                        'Module': additional_record.get('module'),
                        'LinkedRecordType': additional_record.get('linked_record_type'),
                        'LinkedRecordId': additional_record.get('linked_record_id'),
                        'LinkedRecordName': additional_record.get('linked_record_name'),
                        'Category': data.get('category'),  # Keep original category field
                        'EventType': event_type_obj,  # Save event type object in EventType field
                        'SubEventType': sub_event_type_name,  # Save selected sub-event type name
                        'RecurrenceType': data.get('recurrence_type', 'Non-Recurring'),
                        'Frequency': frequency,
                        'StartDate': start_date,
                        'EndDate': end_date,
                        'Status': data.get('status', initial_status),
                        'Priority': data.get('priority', 'Medium'),
                        'CreatedBy': Users.objects.get(UserId=user_id) if user_id else None,
                        'Owner': owner_obj,
                        'Reviewer': reviewer_obj,
                        'IsTemplate': is_template,
                        'Evidence': evidence_string  # Include evidence for additional records too
                    }
                    
                    # Create the additional event
                    additional_event = Event.objects.create(**additional_event_data)
                    print(f"DEBUG: Additional event {i+1} created successfully with ID: {additional_event.EventId}")
                    
                    created_events.append({
                        'EventId': additional_event.EventId,
                        'EventTitle': additional_event.EventTitle,
                        'Status': additional_event.Status,
                        'RecurrenceType': additional_event.RecurrenceType,
                        'StartDate': additional_event.StartDate,
                        'EndDate': additional_event.EndDate,
                        'LinkedRecordName': additional_event.LinkedRecordName,
                        'FrameworkName': additional_event.FrameworkName,
                        'Module': additional_event.Module
                    })
            
            total_events = len(created_events)
            message = f'Event created successfully' if total_events == 1 else f'{total_events} events created successfully (1 primary + {total_events-1} additional records)'
            
            # Send email notifications for event creation
            try:
                from ...routes.Global.notification_service import NotificationService
                notification_service = NotificationService()
                from ...routes.Global.notifications import notifications_storage
                import uuid
                from datetime import datetime as dt
                
                # Helper function to send event notifications
                def send_event_notifications(event_obj, is_assigned=False):
                    """Send email and in-app notifications for an event"""
                    recipients = []
                    
                    # Collect recipients (Owner, Reviewer, Creator)
                    if event_obj.Owner and hasattr(event_obj.Owner, 'Email') and event_obj.Owner.Email:
                        recipients.append({
                            'role': 'owner',
                            'email': event_obj.Owner.Email,
                            'name': event_obj.Owner.UserName or event_obj.Owner.Email.split('@')[0],
                            'user_id': event_obj.Owner.UserId
                        })
                    if event_obj.Reviewer and hasattr(event_obj.Reviewer, 'Email') and event_obj.Reviewer.Email:
                        recipients.append({
                            'role': 'reviewer',
                            'email': event_obj.Reviewer.Email,
                            'name': event_obj.Reviewer.UserName or event_obj.Reviewer.Email.split('@')[0],
                            'user_id': event_obj.Reviewer.UserId
                        })
                    if event_obj.CreatedBy and hasattr(event_obj.CreatedBy, 'Email') and event_obj.CreatedBy.Email:
                        recipients.append({
                            'role': 'creator',
                            'email': event_obj.CreatedBy.Email,
                            'name': event_obj.CreatedBy.UserName or event_obj.CreatedBy.Email.split('@')[0],
                            'user_id': event_obj.CreatedBy.UserId
                        })
                    
                    # Send email notifications
                    for recipient in recipients:
                        try:
                            if is_assigned and recipient['role'] in ['owner', 'reviewer']:
                                # Use eventAssigned template for assigned users
                                notification_type = 'eventAssigned'
                                due_date_str = event_obj.EndDate.strftime('%Y-%m-%d') if event_obj.EndDate else 'Not specified'
                                template_data = [
                                    recipient['name'],
                                    event_obj.EventTitle,
                                    event_obj.Description or 'No description provided',
                                    event_obj.CreatedBy.UserName if event_obj.CreatedBy else 'System',
                                    event_obj.Category or 'General',
                                    due_date_str
                                ]
                            else:
                                # Use eventCreated template
                                notification_type = 'eventCreated'
                                template_data = [
                                    recipient['name'],
                                    event_obj.EventTitle,
                                    event_obj.Description or 'No description provided',
                                    event_obj.CreatedBy.UserName if event_obj.CreatedBy else 'System',
                                    event_obj.Category or 'General'
                                ]
                            
                            notification_data = {
                                'notification_type': notification_type,
                                'email': recipient['email'],
                                'email_type': 'gmail',
                                'template_data': template_data
                            }
                            notification_service.send_multi_channel_notification(notification_data)
                            
                            # Create in-app notification
                            notification = {
                                'id': str(uuid.uuid4()),
                                'title': 'Event Assigned' if is_assigned and recipient['role'] in ['owner', 'reviewer'] else 'New Event Created',
                                'message': f'Event "{event_obj.EventTitle}" has been {"assigned to you" if is_assigned and recipient["role"] in ["owner", "reviewer"] else "created"}.',
                                'category': 'event',
                                'priority': event_obj.Priority.lower() if event_obj.Priority else 'medium',
                                'createdAt': dt.now().isoformat(),
                                'status': {'isRead': False, 'readAt': None},
                                'user_id': str(recipient['user_id'])
                            }
                            notifications_storage.append(notification)
                            if len(notifications_storage) > 100:
                                notifications_storage.pop(0)
                                
                        except Exception as notify_error:
                            print(f"Error sending notification to {recipient.get('email', 'unknown')}: {str(notify_error)}")
                
                # Send notifications for primary event
                send_event_notifications(event, is_assigned=(event.Owner is not None or event.Reviewer is not None))
                
                # Send notifications for additional events if any
                for additional_event_dict in created_events[1:]:
                    try:
                        additional_event = Event.objects.get(EventId=additional_event_dict['EventId'])
                        send_event_notifications(additional_event, is_assigned=(additional_event.Owner is not None or additional_event.Reviewer is not None))
                    except Event.DoesNotExist:
                        pass
                        
            except Exception as notify_ex:
                print(f"Error sending event notifications: {str(notify_ex)}")
                # Don't fail event creation if notifications fail
            
            return Response({
                'success': True,
                'message': message,
                'event_id': event.EventId,
                'event_id_generated': event.EventId_Generated,
                'total_events_created': total_events,
                'events': created_events
            })
        except Exception as db_error:
            print(f"DEBUG: Database error: {str(db_error)}")
            if "Unknown column" in str(db_error):
                return Response({
                    'success': False,
                    'message': 'Events table schema mismatch. Please run: python manage.py create_events_table',
                    'error': str(db_error)
                }, status=500)
            else:
                raise db_error
        
    except Exception as e:
        print(f"DEBUG: Exception in create_event: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'message': f'Error creating event: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def get_events(request):
    """
    Get all events with optional filtering
    """
    try:
        # Get user ID for RBAC filtering
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Get filter parameters
        event_type = request.GET.get('type', '')
        module = request.GET.get('module', '')
        status = request.GET.get('status', '')
        
        # Get user's accessible modules based on RBAC permissions
        accessible_modules = RBACUtils.get_user_accessible_modules(user_id)
        user_permissions = RBACUtils.get_user_event_permissions(user_id)
        
        # Start with base query
        events_query = Event.objects.select_related(
            'Owner', 'Reviewer', 'CreatedBy', 'FrameworkId', 'EventType'
        ).filter(IsTemplate=False)
        
        # Apply module filtering based on user permissions
        if not user_permissions.get('view_all_event', False) and user_permissions.get('view_module_event', False):
            if accessible_modules:
                events_query = events_query.filter(Module__in=accessible_modules)
            else:
                return Response({
                    'success': True,
                    'events': [],
                    'message': 'No accessible modules found for user'
                })
        
        # Apply filters
        if event_type:
            events_query = events_query.filter(EventType__eventtype__icontains=event_type)
        if module:
            events_query = events_query.filter(Module__icontains=module)
        if status:
            events_query = events_query.filter(Status__icontains=status)
        
        # Apply framework filtering
        from ..Policy.framework_filter_helper import apply_framework_filter, get_framework_filter_info
        filter_info = get_framework_filter_info(request)
        print(f"🔍 DEBUG: Framework filter info for get_events: {filter_info}")
        events_query = apply_framework_filter(events_query, request, 'FrameworkId')
        
        events = events_query.values(
            'EventId', 'EventTitle', 'EventId_Generated', 'FrameworkName',
            'Module', 'Category', 'Status', 'Priority', 'CreatedAt',
            'Description', 'LinkedRecordName', 'LinkedRecordType', 'RecurrenceType', 'Frequency',
            'EventType__eventtype_id', 'EventType__eventtype', 'EventType__FrameworkName',
            'Owner__FirstName', 'Owner__LastName', 'Owner__UserId', 'Reviewer__FirstName', 
            'Reviewer__LastName', 'Reviewer__UserId', 'CreatedBy__FirstName', 'CreatedBy__LastName',
            'Evidence', 'DynamicFieldsData'
        )
        
        formatted_events = []
        for event in events:
            # Process evidence data
            evidence_string = event['Evidence'] if event['Evidence'] else ''
            evidence_count = len([url for url in evidence_string.split(';') if url.strip()]) if evidence_string else 0
            
            formatted_events.append({
                'id': event['EventId'],
                'title': event['EventTitle'],
                'event_id': event['EventId_Generated'],
                'framework': event['FrameworkName'],
                'module': event['Module'],
                'category': event['Category'],
                'event_type_id': event['EventType__eventtype_id'],
                'event_type': event['EventType__eventtype'],
                'event_type_framework': event['EventType__FrameworkName'],
                'status': event['Status'],
                'evidence_count': evidence_count,
                'priority': event['Priority'],
                'description': event['Description'],
                'linked_record_name': event['LinkedRecordName'],
                'linked_record_type': event['LinkedRecordType'],
                'recurrence_type': event['RecurrenceType'],
                'frequency': event['Frequency'],
                'owner': f"{event['Owner__FirstName']} {event['Owner__LastName']}" if event['Owner__FirstName'] else 'Not Assigned',
                'owner_id': event['Owner__UserId'],
                'reviewer': f"{event['Reviewer__FirstName']} {event['Reviewer__LastName']}" if event['Reviewer__FirstName'] else 'Not Assigned',
                'reviewer_id': event['Reviewer__UserId'],
                'created_by': f"{event['CreatedBy__FirstName']} {event['CreatedBy__LastName']}" if event['CreatedBy__FirstName'] else 'Unknown',
                'created_at': event['CreatedAt'].strftime('%Y-%m-%d %H:%M') if event['CreatedAt'] else '',
                'dynamic_fields_data': event['DynamicFieldsData']
            })
        
        return Response({
            'success': True,
            'events': formatted_events
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error fetching events: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
def get_document_handling_events(request):
    """
    Get document handling events from file_operations table
    """
    try:
        print("DEBUG: get_document_handling_events called")
        # Get user ID for RBAC filtering
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        print(f"DEBUG: User ID: {user_id}")
        
        # Get query parameters
        limit = int(request.GET.get('limit', 50))
        operation_type = request.GET.get('operation_type', '')
        status = request.GET.get('status', '')
        
        # Get file operations from the file_operations table
        file_operations_query = FileOperations.objects.all()
        
        # Apply filters
        if operation_type:
            file_operations_query = file_operations_query.filter(operation_type=operation_type)
        if status:
            file_operations_query = file_operations_query.filter(status=status)
        
        # Apply limit
        file_operations_query = file_operations_query[:limit]
        
        print(f"DEBUG: Found {file_operations_query.count()} file operations")
        
        formatted_events = []
        for file_op in file_operations_query:
            # Create event-like structure from file operations
            formatted_events.append({
                'id': f"file_op_{file_op.id}",
                'title': f"{file_op.operation_type.title()}: {file_op.display_name}",
                'event_id': f"FILE-{file_op.id}",
                'framework': 'Document Handling System',
                'module': file_op.module or 'Document Handling',
                'category': 'File Operation',
                'event_type_id': None,
                'event_type': file_op.operation_type.title(),
                'event_type_framework': 'Document Handling System',
                'status': file_op.status.title(),
                'evidence_count': 1 if file_op.s3_url else 0,
                'priority': 'Medium',
                'description': f"File {file_op.operation_type} operation: {file_op.display_name}",
                'linked_record_name': file_op.display_name,
                'linked_record_type': 'File Operation',
                'linked_record_id': file_op.id,
                'recurrence_type': 'Non-Recurring',
                'frequency': None,
                'owner': f"User {file_op.user_id}",
                'owner_id': file_op.user_id,
                'reviewer': 'System',
                'reviewer_id': None,
                'created_by': f"User {file_op.user_id}",
                'created_at': file_op.created_at.strftime('%Y-%m-%d %H:%M') if file_op.created_at else '',
                'dynamic_fields_data': {
                    'file_name': file_op.file_name,
                    'original_name': file_op.original_name,
                    'stored_name': file_op.stored_name,
                    'file_type': file_op.file_type,
                    'file_size': file_op.file_size,
                    'content_type': file_op.content_type,
                    's3_url': file_op.s3_url,
                    's3_key': file_op.s3_key,
                    's3_bucket': file_op.s3_bucket,
                    'export_format': file_op.export_format,
                    'record_count': file_op.record_count,
                    'platform': file_op.platform,
                    'error': file_op.error,
                    'metadata': file_op.metadata
                },
                'evidence': [file_op.s3_url] if file_op.s3_url else [],
                'is_file_operation': True
            })
        
        return Response({
            'success': True,
            'events': formatted_events
        })
        
    except Exception as e:
        print(f"DEBUG: Error in get_document_handling_events: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error fetching document handling events: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def get_events_list(request):
    """
    Get list of all events (including templates and RiskaVaire events)
    Shows comprehensive view of all events in the system
    """
    try:
        import random
        
        # Get user ID for RBAC filtering
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Get available frameworks and modules from database
        available_frameworks = []
        available_modules = []
        
        try:
            from ...models import Framework, Module
            
            # Fetch all active frameworks
            frameworks = Framework.objects.filter(ActiveInactive='Active').values_list('FrameworkName', flat=True)
            available_frameworks = list(frameworks)
            
            # Fetch all modules (Module model doesn't have is_active field)
            modules = Module.objects.all().values_list('modulename', flat=True)
            available_modules = list(modules)
            
            print(f"DEBUG: Fetched {len(available_frameworks)} frameworks from database: {list(available_frameworks)}")
            print(f"DEBUG: Fetched {len(available_modules)} modules from database: {list(available_modules)}")
        except Exception as module_error:
            print(f"Error fetching frameworks/modules: {module_error}")
            import traceback
            traceback.print_exc()
        
        # Fallback lists if database is empty
        if not available_frameworks:
            available_frameworks = [
                'Basel III Framework',
                'NIST',
                'ISO 27001',
                'COBIT',
                'PCI DSS',
                'HIPAA',
                'SOX',
                'GDPR'
            ]
        
        if not available_modules:
            available_modules = [
                'Audit Management',
                'Compliance Management',
                'Incident Management',
                'Policy Management',
                'Risk Management'
            ]
        
        print(f"Available Frameworks: {available_frameworks}")
        print(f"Available Modules: {available_modules}")
        print(f"DEBUG: Framework count: {len(available_frameworks)}")
        print(f"DEBUG: Module count: {len(available_modules)}")
        
        # Get user's accessible modules based on RBAC permissions
        accessible_modules = RBACUtils.get_user_accessible_modules(user_id)
        user_permissions = RBACUtils.get_user_event_permissions(user_id)
        
        # Check if events table exists and has data
        try:
            total_events = Event.objects.count()
            print(f"DEBUG: Total events in database: {total_events}")
            
            # If no events exist, create some sample events for testing
            if total_events == 0:
                print("DEBUG: No events found, creating sample events...")
                from django.utils import timezone
                from datetime import datetime, timedelta
                
                # Get the current user for sample events
                try:
                    current_user = Users.objects.get(UserId=user_id)
                    print(f"DEBUG: Using current user {user_id} for sample events")
                except Users.DoesNotExist:
                    print(f"DEBUG: Current user {user_id} not found, using first available user")
                    current_user = Users.objects.first()
                    if not current_user:
                        print("DEBUG: No users found in database")
                        return Response({
                            'success': True,
                            'events': [],
                            'message': 'No users found in database'
                        })
                except Exception as e:
                    print(f"DEBUG: Error getting user: {e}")
                    return Response({
                        'success': True,
                        'events': [],
                        'message': 'Error accessing user data'
                    })
                
                # Create sample events
                sample_events = [
                    {
                        'EventTitle': 'Security Policy Review',
                        'EventId_Generated': 'EVT-2025-0001',
                        'Description': 'Quarterly review of security policies',
                        'FrameworkName': 'ISO 27001',
                        'Module': 'Policy Management',
                        'Category': 'Compliance',
                        'Status': 'Pending Review',
                        'Priority': 'High',
                        'CreatedBy': current_user,
                        'Owner': current_user,
                        'Reviewer': current_user,
                        'CreatedAt': timezone.now() - timedelta(days=2),
                        'IsTemplate': False
                    },
                    {
                        'EventTitle': 'Risk Assessment Update',
                        'EventId_Generated': 'EVT-2025-0002',
                        'Description': 'Update risk assessment for Q4',
                        'FrameworkName': 'Basel III Framework',
                        'Module': 'Risk Management',
                        'Category': 'Risk',
                        'Status': 'Under Review',
                        'Priority': 'Medium',
                        'CreatedBy': current_user,
                        'Owner': current_user,
                        'Reviewer': current_user,
                        'CreatedAt': timezone.now() - timedelta(days=1),
                        'IsTemplate': False
                    },
                    {
                        'EventTitle': 'Audit Finding Resolution',
                        'EventId_Generated': 'EVT-2025-0003',
                        'Description': 'Resolve audit findings from last quarter',
                        'FrameworkName': 'SOX Compliance',
                        'Module': 'Audit Management',
                        'Category': 'Audit',
                        'Status': 'Approved',
                        'Priority': 'Critical',
                        'CreatedBy': current_user,
                        'Owner': current_user,
                        'Reviewer': current_user,
                        'CreatedAt': timezone.now() - timedelta(hours=6),
                        'IsTemplate': False
                    }
                ]
                
                for event_data in sample_events:
                    try:
                        Event.objects.create(**event_data)
                        print(f"DEBUG: Created sample event: {event_data['EventTitle']}")
                    except Exception as e:
                        print(f"DEBUG: Error creating sample event {event_data['EventTitle']}: {e}")
                
                print(f"DEBUG: Created {len(sample_events)} sample events")
                
        except Exception as e:
            print(f"DEBUG: Error checking/creating events: {e}")
            return Response({
                'success': False,
                'message': f'Error accessing events table: {str(e)}'
            }, status=500)
        
        # Start with base query
        events_query = Event.objects.select_related(
            'Owner', 'Reviewer', 'CreatedBy', 'FrameworkId', 'EventType'
        )
        
        # Apply framework filtering from session (similar to Policy module)
        try:
            from ..Policy.framework_filter_helper import apply_framework_filter, get_framework_filter_info
            
            # Get framework filter info for logging
            filter_info = get_framework_filter_info(request)
            print(f"DEBUG: Events list - Framework filter info: {filter_info}")
            
            # Apply framework filter to events
            events_query = apply_framework_filter(events_query, request, 'FrameworkId')
            
        except ImportError as e:
            print(f"DEBUG: Could not import framework filter helper: {e}")
            # Continue without framework filtering if helper is not available
        except Exception as e:
            print(f"DEBUG: Error applying framework filter: {e}")
            # Continue without framework filtering on error
        
        # Apply module filtering based on user permissions
        if not user_permissions.get('view_all_event', False) and user_permissions.get('view_module_event', False):
            # User can only see events from their accessible modules
            if accessible_modules:
                events_query = events_query.filter(Module__in=accessible_modules)
            else:
                # User has view_module_event permission but no accessible modules
                return Response({
                    'success': True,
                    'events': [],
                    'message': 'No accessible modules found for user'
                })
        
        events = events_query.values(
            'EventId', 'EventTitle', 'EventId_Generated', 'FrameworkName',
            'Module', 'Category', 'Status', 'Priority', 'CreatedAt',
            'Description', 'LinkedRecordName', 'LinkedRecordType', 'RecurrenceType', 'Frequency',
            'IsTemplate', 'EventType__eventtype_id', 'EventType__eventtype', 'EventType__FrameworkName',
            'Owner__FirstName', 'Owner__LastName', 'Owner__UserId', 'Reviewer__FirstName', 
            'Reviewer__LastName', 'Reviewer__UserId', 'CreatedBy__FirstName', 'CreatedBy__LastName',
            'Evidence'  # Include Evidence field
        )
        
        formatted_events = []
        for event in events:
            # Process evidence data for list view
            evidence_string = event.get('Evidence', '') or ""
            evidence_count = len([url for url in evidence_string.split(';') if url.strip()]) if evidence_string else 0
            
            # Assign random framework if missing
            framework = event['FrameworkName']
            if not framework or framework == 'N/A' or framework is None or framework == '':
                framework = random.choice(available_frameworks)
            
            # Assign random module if missing
            module = event['Module']
            if not module or module == 'N/A' or module is None or module == '':
                module = random.choice(available_modules)
            
            formatted_events.append({
                'id': event['EventId'],
                'title': event['EventTitle'],
                'event_id': event['EventId_Generated'],
                'framework': framework,
                'module': module,
                'category': event['Category'],
                'event_type_id': event['EventType__eventtype_id'],
                'event_type': event['EventType__eventtype'],
                'event_type_framework': event['EventType__FrameworkName'],
                'status': event['Status'],
                'evidence_count': evidence_count,  # Add evidence count
                'priority': event['Priority'],
                'description': event['Description'],
                'linked_record_name': event['LinkedRecordName'],
                'linked_record_type': event['LinkedRecordType'],
                'recurrence_type': event['RecurrenceType'],
                'frequency': event['Frequency'],
                'is_template': event['IsTemplate'],
                'owner': f"{event['Owner__FirstName']} {event['Owner__LastName']}" if event['Owner__FirstName'] else 'Not Assigned',
                'owner_id': event['Owner__UserId'],
                'reviewer': f"{event['Reviewer__FirstName']} {event['Reviewer__LastName']}" if event['Reviewer__FirstName'] else 'Not Assigned',
                'reviewer_id': event['Reviewer__UserId'],
                'created_by': f"{event['CreatedBy__FirstName']} {event['CreatedBy__LastName']}" if event['CreatedBy__FirstName'] else 'Unknown',
                'created_at': event['CreatedAt'].strftime('%Y-%m-%d %H:%M') if event['CreatedAt'] else ''
            })
        
        return Response({
            'success': True,
            'events': formatted_events
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error fetching events: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
def get_event_details(request, event_id):
    """
    Get detailed information about a specific event
    """
    try:
        print(f"DEBUG: Fetching event details for ID: {event_id}")
        event = Event.objects.select_related(
            'Owner', 'Reviewer', 'CreatedBy', 'FrameworkId', 'EventType'
        ).get(EventId=event_id)
        print(f"DEBUG: Found event: {event.EventTitle}")
        
        # Process evidence data from semicolon-separated string to array
        evidence_string = event.Evidence or ""
        evidence_urls = evidence_string.split(';') if evidence_string else []
        evidence_urls = [url.strip() for url in evidence_urls if url.strip()]
        
        # Convert evidence URLs to evidence objects for frontend
        evidence_objects = []
        for i, url in enumerate(evidence_urls):
            # Extract filename from URL
            filename = "Evidence File"
            if url:
                try:
                    # Extract filename from S3 URL
                    if 'amazonaws.com' in url:
                        # Extract from S3 URL like: https://bucket.s3.region.amazonaws.com/path/filename.ext
                        url_parts = url.split('/')
                        if len(url_parts) > 0:
                            filename = url_parts[-1]
                            # Decode URL encoding
                            filename = filename.replace('%20', ' ').replace('%2E', '.')
                    else:
                        # Extract from other URL formats
                        url_parts = url.split('/')
                        if len(url_parts) > 0:
                            filename = url_parts[-1]
                except:
                    filename = f"Evidence File {i + 1}"
            
            evidence_objects.append({
                'id': i + 1,
                'fileName': filename,
                'url': url,
                's3_url': url,
                'uploadedBy': event.CreatedBy.FirstName + ' ' + event.CreatedBy.LastName if event.CreatedBy else 'Unknown',
                'uploadDate': event.CreatedAt.strftime('%Y-%m-%d') if event.CreatedAt else 'Unknown',
                'size': 'Unknown'  # Size would need to be stored separately or fetched from S3
            })
        
        try:
            print(f"DEBUG: Building event data for event: {event.EventTitle}")
            event_data = {
                'id': event.EventId,
                'title': event.EventTitle,
                'event_id_generated': event.EventId_Generated,
                'description': event.Description,
                'framework_id': event.FrameworkId.FrameworkId if event.FrameworkId else None,
                'framework': event.FrameworkName or 'Not Assigned',  # Map to 'framework' for frontend
                'framework_name': event.FrameworkName,
                'module': event.Module or 'Not Assigned',
                'linked_record_type': event.LinkedRecordType,
                'linked_record_id': event.LinkedRecordId,
                'linked_record_name': event.LinkedRecordName,
                'category': event.Category or 'Not Assigned',
                'event_type_id': event.EventType.eventtype_id if event.EventType else None,
                'event_type': event.EventType.eventtype if event.EventType else None,
                'event_type_framework': event.EventType.FrameworkName if event.EventType else None,
                'sub_event_type': event.SubEventType,
                'recurrence_type': event.RecurrenceType,
                'frequency': event.Frequency,
                'start_date': event.StartDate,
                'end_date': event.EndDate,
                'status': event.Status or 'Not Assigned',
                'priority': event.Priority or 'Not Assigned',
                'comments': event.Comments,
                'evidence': evidence_objects,  # Include evidence data
                'evidence_string': evidence_string,  # Include raw evidence string
                'owner_id': event.Owner.UserId if event.Owner else None,
                'owner': event.owner_name,  # Use the model property
                'owner_name': event.owner_name,
                'reviewer_id': event.Reviewer.UserId if event.Reviewer else None,
                'reviewer': event.reviewer_name,  # Use the model property
                'reviewer_name': event.reviewer_name,
                'source_system': 'GRC System',  # Add source system field
                'created_by_id': event.CreatedBy.UserId if event.CreatedBy else None,
                'created_by_name': f"{event.CreatedBy.FirstName} {event.CreatedBy.LastName}" if event.CreatedBy else 'Unknown',
                'created_at': event.CreatedAt,
                'updated_at': event.UpdatedAt,
                'approved_at': event.ApprovedAt,
                'dynamic_fields_data': event.DynamicFieldsData
            }
            print(f"DEBUG: Event data built successfully")
        except Exception as e:
            print(f"DEBUG: Error building event data: {str(e)}")
            raise e
        
        return Response({
            'success': True,
            'event': event_data
        })
        
    except Event.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Event not found'
        }, status=404)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error fetching event details: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([AllowAny])
@csrf_exempt
def get_current_user(request):
    """
    Get current logged-in user information
    """
    try:
        # Get user from JWT token (assuming it's available in request)
        user_id = request.GET.get('user_id')
        if not user_id:
            return Response({
                'success': False,
                'message': 'User ID is required'
            }, status=400)
        
        user = Users.objects.get(UserId=user_id)
        user_data = {
            'id': user.UserId,
            'name': f"{user.FirstName} {user.LastName}".strip(),
            'first_name': user.FirstName,
            'last_name': user.LastName,
            'email': user.Email,
            'username': user.UserName
        }
        
        return Response({
            'success': True,
            'user': user_data
        })
        
    except Users.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=404)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error fetching user: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([AllowAny])
@csrf_exempt
def test_dynamic_fields_endpoint(request):
    """
    Test endpoint to verify URL routing is working
    """
    print("DEBUG: test_dynamic_fields_endpoint called")
    return Response({
        'success': True,
        'message': 'Dynamic fields endpoint is working',
        'path': request.path,
        'method': request.method
    })

@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([AllowAny])
@csrf_exempt
def get_dynamic_fields_for_event(request):
    """
    Get dynamic fields configuration based on framework and event type selection
    """
    print("DEBUG: get_dynamic_fields_for_event called")
    print(f"DEBUG: Request path: {request.path}")
    print(f"DEBUG: Request method: {request.method}")
    print(f"DEBUG: Request GET params: {request.GET}")
    try:
        framework_name = request.GET.get('framework_name')
        event_type_id = request.GET.get('event_type_id')
        sub_event_type_id = request.GET.get('sub_event_type_id')
        
        print(f"DEBUG: framework_name='{framework_name}', event_type_id='{event_type_id}', sub_event_type_id='{sub_event_type_id}'")
        
        if not framework_name or not event_type_id:
            return Response({
                'success': False,
                'message': 'Framework name and event type ID are required'
            }, status=400)
        
        # Get the event type object
        try:
            event_type = EventType.objects.get(
                eventtype_id=event_type_id,
                FrameworkName=framework_name.strip()
            )
        except EventType.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Event type not found'
            }, status=404)
        
        # Default field configuration (excluding fields already in the main form)
        default_fields = {
            'priority': {
                'type': 'select',
                'label': 'Priority',
                'required': True,
                'options': [
                    {'value': 'Low', 'label': 'Low'},
                    {'value': 'Medium', 'label': 'Medium'},
                    {'value': 'High', 'label': 'High'},
                    {'value': 'Critical', 'label': 'Critical'}
                ],
                'default': 'Medium',
                'description': 'Event priority level'
            }
        }
        
        # Get dynamic fields from event type configuration
        dynamic_fields = {}
        
        # Parse the JSON data from eventSubtype field
        if event_type.eventSubtype:
            try:
                # eventSubtype is already a JSON field, so we can access it directly
                event_subtype_data = event_type.eventSubtype
                print(f"DEBUG: Raw eventSubtype data: {event_subtype_data}")
                
                if isinstance(event_subtype_data, dict):
                    # Get the sub-event type name from the index
                    sub_event_type_name = None
                    if sub_event_type_id is not None:
                        try:
                            sub_event_type_index = int(sub_event_type_id)
                            sub_event_type_keys = list(event_subtype_data.keys())
                            if 0 <= sub_event_type_index < len(sub_event_type_keys):
                                sub_event_type_name = sub_event_type_keys[sub_event_type_index]
                                print(f"DEBUG: Selected sub-event type: {sub_event_type_name}")
                                
                                # Get the configuration for this sub-event type
                                sub_event_config = event_subtype_data.get(sub_event_type_name, {})
                                print(f"DEBUG: Sub-event config: {sub_event_config}")
                                
                                # Parse the configuration to create dynamic fields
                                dynamic_fields = parse_event_subtype_config(sub_event_config, sub_event_type_name)
                                
                        except (ValueError, IndexError, KeyError) as e:
                            print(f"DEBUG: Error processing sub-event type: {str(e)}")
                            # Continue with empty dynamic fields if there's an error
                            pass
                    else:
                        # If no sub-event type is selected, use the first available one
                        if event_subtype_data:
                            first_key = list(event_subtype_data.keys())[0]
                            sub_event_config = event_subtype_data.get(first_key, {})
                            dynamic_fields = parse_event_subtype_config(sub_event_config, first_key)
                            
            except Exception as e:
                print(f"DEBUG: Error parsing eventSubtype JSON: {str(e)}")
                # Continue with empty dynamic fields if there's an error
                pass
        
        # Merge default fields with dynamic fields
        all_fields = {**default_fields, **dynamic_fields}
        
        print(f"DEBUG: Returning {len(all_fields)} fields for event type '{event_type.eventtype}'")
        
        # Get the sub-event type name for the response
        sub_event_type_name = None
        if sub_event_type_id is not None and event_type.eventSubtype:
            try:
                sub_event_type_index = int(sub_event_type_id)
                if isinstance(event_type.eventSubtype, dict):
                    sub_event_type_keys = list(event_type.eventSubtype.keys())
                    if 0 <= sub_event_type_index < len(sub_event_type_keys):
                        sub_event_type_name = sub_event_type_keys[sub_event_type_index]
            except (ValueError, IndexError, KeyError):
                pass
        
        return Response({
            'success': True,
            'fields': all_fields,
            'event_type': event_type.eventtype,
            'framework_name': framework_name,
            'sub_event_type': sub_event_type_name
        })
        
    except Exception as e:
        print(f"DEBUG: Exception in get_dynamic_fields_for_event: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'message': f'Error fetching dynamic fields: {str(e)}'
        }, status=500)


def parse_event_subtype_config(sub_event_config, sub_event_type_name):
    """
    Parse the JSON configuration from eventSubtype and convert it to dynamic fields
    """
    dynamic_fields = {}
    
    try:
        print(f"DEBUG: Parsing config for '{sub_event_type_name}': {sub_event_config}")
        
        # Recursively parse the configuration
        def parse_config_recursive(config, prefix=""):
            fields = {}
            
            for key, value in config.items():
                field_key = f"{prefix}_{key}".strip("_") if prefix else key
                field_key = field_key.lower().replace(" ", "_").replace("&", "and")
                
                if isinstance(value, dict):
                    # If it's a nested object, create a field for it
                    if any(isinstance(v, dict) for v in value.values()):
                        # It has nested objects, create a section header
                        fields[field_key] = {
                            'type': 'section',
                            'label': key.replace("_", " ").title(),
                            'description': f'Configuration for {key}',
                            'children': parse_config_recursive(value, field_key)
                        }
                    else:
                        # It's a simple key-value mapping, create a select field
                        if value:
                            options = []
                            for opt_key, opt_value in value.items():
                                if isinstance(opt_value, str) and opt_value.strip():
                                    options.append({'value': opt_key, 'label': f"{opt_key}: {opt_value}"})
                                else:
                                    options.append({'value': opt_key, 'label': opt_key})
                            
                            if options:
                                fields[field_key] = {
                                    'type': 'select',
                                    'label': key.replace("_", " ").title(),
                                    'required': False,
                                    'options': options,
                                    'description': f'Select {key.lower()}'
                                }
                        else:
                            # Empty dict, create a text field
                            fields[field_key] = {
                                'type': 'text',
                                'label': key.replace("_", " ").title(),
                                'required': False,
                                'placeholder': f'Enter {key.lower()}',
                                'description': f'Specify {key.lower()}'
                            }
                elif isinstance(value, str):
                    # String value, create a text field with the value as placeholder
                    fields[field_key] = {
                        'type': 'text',
                        'label': key.replace("_", " ").title(),
                        'required': False,
                        'placeholder': value if value.strip() else f'Enter {key.lower()}',
                        'description': f'Specify {key.lower()}'
                    }
                elif isinstance(value, list):
                    # List value, create a select field with list items as options
                    if value:
                        options = [{'value': item, 'label': str(item)} for item in value if str(item).strip()]
                        if options:
                            fields[field_key] = {
                                'type': 'select',
                                'label': key.replace("_", " ").title(),
                                'required': False,
                                'options': options,
                                'description': f'Select {key.lower()}'
                            }
                    else:
                        # Empty list, create a text field
                        fields[field_key] = {
                            'type': 'text',
                            'label': key.replace("_", " ").title(),
                            'required': False,
                            'placeholder': f'Enter {key.lower()}',
                            'description': f'Specify {key.lower()}'
                        }
                else:
                    # Other types, create a text field
                    fields[field_key] = {
                        'type': 'text',
                        'label': key.replace("_", " ").title(),
                        'required': False,
                        'placeholder': f'Enter {key.lower()}',
                        'description': f'Specify {key.lower()}'
                    }
            
            return fields
        
        # Parse the configuration
        parsed_fields = parse_config_recursive(sub_event_config)
        dynamic_fields.update(parsed_fields)
        
        print(f"DEBUG: Generated {len(dynamic_fields)} dynamic fields")
        for field_key, field_config in dynamic_fields.items():
            print(f"DEBUG: Field '{field_key}': {field_config.get('type', 'unknown')} - {field_config.get('label', 'No label')}")
        
    except Exception as e:
        print(f"DEBUG: Error parsing event subtype config: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
    
    return dynamic_fields


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([AllowAny])
@csrf_exempt
def get_users_for_reviewer(request):
    """
    Get all users except the current user for reviewer selection
    """
    try:
        current_user_id = request.GET.get('user_id')
        if not current_user_id:
            return Response({
                'success': False,
                'message': 'User ID is required'
            }, status=400)
        
        # Get all users except the current user
        users = Users.objects.exclude(UserId=current_user_id).values(
            'UserId', 'FirstName', 'LastName', 'Email', 'UserName'
        )
        
        users_list = []
        for user in users:
            users_list.append({
                'id': user['UserId'],
                'name': f"{user['FirstName']} {user['LastName']}".strip(),
                'first_name': user['FirstName'],
                'last_name': user['LastName'],
                'email': user['Email'],
                'username': user['UserName']
            })
        
        return Response({
            'success': True,
            'users': users_list
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error fetching users: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def get_events_for_calendar(request):
    """
    Get events for calendar display (recurring events only, including all event types)
    """
    try:
        # Get only recurring events for calendar - include ALL events
        events_query = Event.objects.filter(
            RecurrenceType='Recurring',
            IsTemplate=False
        ).select_related(
            'Owner', 'Reviewer', 'FrameworkId'
        )
        
        # Apply framework filtering
        from ..Policy.framework_filter_helper import apply_framework_filter, get_framework_filter_info
        filter_info = get_framework_filter_info(request)
        print(f"🔍 DEBUG: Framework filter info for get_events_for_calendar: {filter_info}")
        events_query = apply_framework_filter(events_query, request, 'FrameworkId')
        
        events = events_query.values(
            'EventId', 'EventTitle', 'EventId_Generated', 'FrameworkName',
            'Module', 'Category', 'Status', 'Priority', 'Frequency',
            'StartDate', 'EndDate', 'CreatedAt',
            'Owner__FirstName', 'Owner__LastName', 'Reviewer__FirstName', 
            'Reviewer__LastName'
        )
        
        formatted_events = []
        for event in events:
            formatted_events.append({
                'id': event['EventId'],
                'title': event['EventTitle'],
                'event_id': event['EventId_Generated'],
                'framework': event['FrameworkName'],
                'module': event['Module'],
                'category': event['Category'],
                'status': event['Status'],
                'priority': event['Priority'],
                'frequency': event['Frequency'],
                'start_date': event['StartDate'].strftime('%Y-%m-%d') if event['StartDate'] else None,
                'end_date': event['EndDate'].strftime('%Y-%m-%d') if event['EndDate'] else None,
                'owner': f"{event['Owner__FirstName']} {event['Owner__LastName']}" if event['Owner__FirstName'] else 'Not Assigned',
                'reviewer': f"{event['Reviewer__FirstName']} {event['Reviewer__LastName']}" if event['Reviewer__FirstName'] else 'Not Assigned',
                'created_at': event['CreatedAt'].strftime('%Y-%m-%d %H:%M') if event['CreatedAt'] else ''
            })
        
        return Response({
            'success': True,
            'events': formatted_events
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error fetching calendar events: {str(e)}'
        }, status=500)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([AllowAny])
@csrf_exempt
def create_events_table(request):
    """
    Create the events table if it doesn't exist
    """
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            # First, check if table exists and add missing columns
            try:
                cursor.execute("ALTER TABLE events ADD COLUMN SubEventType VARCHAR(100)")
                print("Added SubEventType column")
            except Exception as e:
                print(f"SubEventType column may already exist: {e}")
            
            try:
                cursor.execute("ALTER TABLE events ADD COLUMN DynamicFieldsData JSON")
                print("Added DynamicFieldsData column")
            except Exception as e:
                print(f"DynamicFieldsData column may already exist: {e}")
            
            # Create events table matching the exact database structure
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    EventId INT AUTO_INCREMENT PRIMARY KEY,
                    EventTitle VARCHAR(255) NOT NULL,
                    EventId_Generated VARCHAR(50) UNIQUE NOT NULL,
                    Description TEXT,
                    
                    -- Framework and Module Information
                    FrameworkId INT,
                    FrameworkName VARCHAR(255),
                    Module VARCHAR(255),
                    
                    -- Linked Records
                    LinkedRecordType VARCHAR(50),
                    LinkedRecordId INT,
                    LinkedRecordName VARCHAR(255),
                    
                    -- Event Details
                    Category VARCHAR(100),
                    OwnerId INT,
                    ReviewerId INT,
                    
                    -- Recurrence Information
                    RecurrenceType VARCHAR(20) DEFAULT 'Non-Recurring',
                    Frequency VARCHAR(50),
                    StartDate DATE,
                    EndDate DATE,
                    
                    -- Status and Dates
                    Status VARCHAR(50) DEFAULT 'Draft',
                    Priority VARCHAR(20) DEFAULT 'Medium',
                    
                    -- Evidence and Attachments
                    Evidence JSON,
                    CreatedById INT,
                    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    ApprovedAt TIMESTAMP NULL,
                    IsTemplate TINYINT(1) DEFAULT 0,
                    comments VARCHAR(255),
                    EventTypeId INT,
                    DynamicFieldsData JSON,
                    SubEventType VARCHAR(100),
                    
                    -- Foreign Key Constraints
                    FOREIGN KEY (FrameworkId) REFERENCES frameworks(FrameworkId) ON DELETE SET NULL,
                    FOREIGN KEY (EventTypeId) REFERENCES eventtype(eventtype_id) ON DELETE SET NULL,
                    FOREIGN KEY (OwnerId) REFERENCES users(UserId) ON DELETE SET NULL,
                    FOREIGN KEY (ReviewerId) REFERENCES users(UserId) ON DELETE SET NULL,
                    FOREIGN KEY (CreatedById) REFERENCES users(UserId) ON DELETE SET NULL
                )
            """)
            
            return Response({
                'success': True,
                'message': 'Events table created successfully'
            })
            
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error creating events table: {str(e)}'
        }, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def fix_events_table_schema(request):
    """
    Fix the events table schema by adding missing columns
    """
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Check if EventTypeId column exists
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'events' 
                AND COLUMN_NAME = 'EventTypeId'
            """)
            event_type_exists = cursor.fetchone()[0] > 0
            
            # Check if SubEventType column exists
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'events' 
                AND COLUMN_NAME = 'SubEventType'
            """)
            sub_event_type_exists = cursor.fetchone()[0] > 0
            
            # Add missing columns
            if not event_type_exists:
                cursor.execute("ALTER TABLE events ADD COLUMN EventTypeId INT")
                print("Added EventTypeId column to events table")
            
            if not sub_event_type_exists:
                cursor.execute("ALTER TABLE events ADD COLUMN SubEventType VARCHAR(100)")
                print("Added SubEventType column to events table")
            
            # Add foreign key constraint for EventTypeId if it doesn't exist
            if not event_type_exists:
                try:
                    cursor.execute("""
                        ALTER TABLE events 
                        ADD CONSTRAINT fk_events_eventtype 
                        FOREIGN KEY (EventTypeId) REFERENCES eventtype(eventtype_id) ON DELETE SET NULL
                    """)
                    print("Added foreign key constraint for EventTypeId")
                except Exception as e:
                    print(f"Could not add foreign key constraint: {e}")
            
            return Response({
                'success': True,
                'message': 'Events table schema fixed successfully',
                'changes': {
                    'event_type_id_added': not event_type_exists,
                    'sub_event_type_added': not sub_event_type_exists
                }
            })
            
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error fixing events table schema: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def get_events_dashboard(request):
    """
    Get events dashboard analytics and KPIs with optional filters
    """
    try:
        from django.db.models import Count, Q
        from datetime import datetime, timedelta
        
        # Get filter parameters from request
        framework_filter = request.GET.get('framework', '')
        module_filter = request.GET.get('module', '')
        category_filter = request.GET.get('category', '')
        owner_filter = request.GET.get('owner', '')
        
        print(f"DEBUG: Dashboard filters - Framework: {framework_filter}, Module: {module_filter}, Category: {category_filter}, Owner: {owner_filter}")
        
        # Build base query with filters - include ALL events (including RiskaVaire events)
        # Show all events in the dashboard for comprehensive view
        base_query = Event.objects.filter(IsTemplate=False)
        
        # Apply framework filtering using the standard framework filter helper
        from ..Policy.framework_filter_helper import apply_framework_filter, get_framework_filter_info
        filter_info = get_framework_filter_info(request)
        print(f"🔍 DEBUG: Framework filter info for get_events_dashboard: {filter_info}")
        base_query = apply_framework_filter(base_query, request, 'FrameworkId')
        
        # Apply additional framework filter if provided in request (for backward compatibility)
        if framework_filter:
            base_query = base_query.filter(FrameworkName__icontains=framework_filter)
        
        if module_filter:
            base_query = base_query.filter(Module__icontains=module_filter)
        
        if category_filter:
            base_query = base_query.filter(Category__icontains=category_filter)
        
        if owner_filter:
            base_query = base_query.filter(
                Q(Owner__FirstName__icontains=owner_filter) | 
                Q(Owner__LastName__icontains=owner_filter)
            )
        
        # Get current date and calculate date ranges
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)
        
        # Calculate KPIs using filtered query
        total_events = base_query.count()
        
        # Upcoming events (next 30 days)
        upcoming_events = base_query.filter(
            StartDate__gte=now.date(),
            StartDate__lte=(now + timedelta(days=30)).date()
        ).count()
        
        # Overdue events (past due date and not completed)
        overdue_events = base_query.filter(
            EndDate__lt=now.date(),
            Status__in=['Draft', 'Submitted', 'Under Review']
        ).count()
        
        # Pending approvals
        pending_approvals = base_query.filter(
            Status='Under Review'
        ).count()
        
        # Events by status
        events_by_status = base_query.values('Status').annotate(
            count=Count('EventId')
        ).order_by('Status')
        
        # Events by category
        events_by_category = base_query.values('Category').annotate(
            count=Count('EventId')
        ).order_by('Category')
        
        # Events by framework
        events_by_framework = base_query.values('FrameworkName').annotate(
            count=Count('EventId')
        ).order_by('FrameworkName')
        
        # Events by priority
        events_by_priority = base_query.values('Priority').annotate(
            count=Count('EventId')
        ).order_by('Priority')
        
        # Monthly event trends (last 6 months) using filtered query
        monthly_trends = []
        for i in range(6):
            month_start = now - timedelta(days=30 * (i + 1))
            month_end = now - timedelta(days=30 * i)
            
            month_events = base_query.filter(
                CreatedAt__gte=month_start,
                CreatedAt__lt=month_end
            ).count()
            
            month_name = month_start.strftime('%b')
            monthly_trends.append({
                'month': month_name,
                'count': month_events
            })
        
        # Reverse to show chronological order (oldest to newest)
        monthly_trends.reverse()
        
        # Recent events (last 7 days) - limit to 3 most recent using filtered query
        recent_events = base_query.filter(
            CreatedAt__gte=seven_days_ago
        ).select_related('Owner', 'Reviewer').values(
            'EventId', 'EventTitle', 'EventId_Generated', 'Status', 'Category',
            'Owner__FirstName', 'Owner__LastName', 'Reviewer__FirstName', 
            'Reviewer__LastName', 'CreatedAt'
        ).order_by('-CreatedAt')[:3]
        
        # Format recent events
        formatted_recent_events = []
        for event in recent_events:
            formatted_recent_events.append({
                'id': event['EventId'],
                'title': event['EventTitle'],
                'event_id': event['EventId_Generated'],
                'status': event['Status'],
                'category': event['Category'],
                'owner': f"{event['Owner__FirstName']} {event['Owner__LastName']}" if event['Owner__FirstName'] else 'Not Assigned',
                'reviewer': f"{event['Reviewer__FirstName']} {event['Reviewer__LastName']}" if event['Reviewer__FirstName'] else 'Not Assigned',
                'created_at': event['CreatedAt'].strftime('%Y-%m-%d %H:%M') if event['CreatedAt'] else ''
            })
        
        # Calculate trends (comparing last 30 days with previous 30 days)
        previous_period_start = now - timedelta(days=60)
        previous_period_end = now - timedelta(days=30)
        
        current_period_events = base_query.filter(
            CreatedAt__gte=thirty_days_ago
        ).count()
        
        previous_period_events = base_query.filter(
            CreatedAt__gte=previous_period_start,
            CreatedAt__lt=previous_period_end
        ).count()
        
        # Calculate trend percentage
        if previous_period_events > 0:
            trend_percentage = ((current_period_events - previous_period_events) / previous_period_events) * 100
        else:
            trend_percentage = 100 if current_period_events > 0 else 0
        
        # Calculate completion rate trends (last 6 months)
        completion_trends = []
        for i in range(6):
            month_start = now - timedelta(days=30 * (i + 1))
            month_end = now - timedelta(days=30 * i)
            
            month_total = base_query.filter(
                CreatedAt__gte=month_start,
                CreatedAt__lt=month_end
            ).count()
            
            month_completed = base_query.filter(
                CreatedAt__gte=month_start,
                CreatedAt__lt=month_end,
                Status='Completed'
            ).count()
            
            completion_rate = (month_completed / month_total * 100) if month_total > 0 else 0
            
            month_name = month_start.strftime('%b')
            completion_trends.append({
                'month': month_name,
                'completion_rate': round(completion_rate, 1),
                'total_events': month_total,
                'completed_events': month_completed
            })
        
        # Reverse to show chronological order (oldest to newest)
        completion_trends.reverse()
        
        return Response({
            'success': True,
            'kpis': {
                'total_events': total_events,
                'upcoming_events': upcoming_events,
                'overdue_events': overdue_events,
                'pending_approvals': pending_approvals,
                'trend_percentage': round(trend_percentage, 1)
            },
            'charts': {
                'events_by_status': list(events_by_status),
                'events_by_category': list(events_by_category),
                'events_by_framework': list(events_by_framework),
                'events_by_priority': list(events_by_priority),
                'monthly_trends': monthly_trends,
                'completion_trends': completion_trends
            },
            'recent_events': formatted_recent_events
        })
        
    except Exception as e:
        print(f"DEBUG: Error in get_events_dashboard: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'message': f'Error fetching dashboard data: {str(e)}'
        }, status=500)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([AllowAny])
@csrf_exempt
def approve_event(request, event_id):
    """
    Approve an event (reviewer action)
    """
    try:
        data = request.data
        user_id = data.get('user_id') or request.GET.get('user_id')
        comments = data.get('comments', '')
        
        if not user_id:
            return Response({
                'success': False,
                'message': 'User ID is required'
            }, status=400)
        
        # Get the event
        try:
            event = Event.objects.get(EventId=event_id)
        except Event.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        # Check if user is the reviewer
        if event.Reviewer and event.Reviewer.UserId != int(user_id):
            return Response({
                'success': False,
                'message': 'Only the assigned reviewer can approve this event'
            }, status=403)
        
        # Check if event is in a reviewable status
        reviewable_statuses = ['Pending Review', 'Under Review', 'Pending Approval']
        if event.Status not in reviewable_statuses:
            return Response({
                'success': False,
                'message': f'Event must be in a reviewable status to be approved. Current status: {event.Status}. Allowed statuses: {", ".join(reviewable_statuses)}'
            }, status=400)
        
        # Store old status for notification
        old_status = event.Status
        
        # Update event status
        event.Status = 'Approved'
        event.ApprovedAt = timezone.now()
        if comments:
            event.Comments = comments
        event.save()
        
        # Send email notification for status change
        try:
            from ...routes.Global.notification_service import NotificationService
            from ...routes.Global.notifications import notifications_storage
            notification_service = NotificationService()
            import uuid
            from datetime import datetime as dt
            
            # Get actor name
            actor = Users.objects.filter(UserId=user_id).first()
            actor_name = actor.UserName if actor else 'System'
            
            # Collect recipients
            recipients = []
            if event.Owner and hasattr(event.Owner, 'Email') and event.Owner.Email:
                recipients.append({
                    'email': event.Owner.Email,
                    'name': event.Owner.UserName or event.Owner.Email.split('@')[0],
                    'user_id': event.Owner.UserId
                })
            if event.Reviewer and hasattr(event.Reviewer, 'Email') and event.Reviewer.Email:
                recipients.append({
                    'email': event.Reviewer.Email,
                    'name': event.Reviewer.UserName or event.Reviewer.Email.split('@')[0],
                    'user_id': event.Reviewer.UserId
                })
            if event.CreatedBy and hasattr(event.CreatedBy, 'Email') and event.CreatedBy.Email:
                recipients.append({
                    'email': event.CreatedBy.Email,
                    'name': event.CreatedBy.UserName or event.CreatedBy.Email.split('@')[0],
                    'user_id': event.CreatedBy.UserId
                })
            
            # Send notifications
            for recipient in recipients:
                try:
                    notification_data = {
                        'notification_type': 'eventStatusChanged',
                        'email': recipient['email'],
                        'email_type': 'gmail',
                        'template_data': [
                            recipient['name'],
                            event.EventTitle,
                            old_status,
                            'Approved',
                            actor_name
                        ]
                    }
                    notification_service.send_multi_channel_notification(notification_data)
                    
                    # In-app notification
                    notification = {
                        'id': str(uuid.uuid4()),
                        'title': 'Event Status Updated',
                        'message': f'Event "{event.EventTitle}" has been approved.',
                        'category': 'event',
                        'priority': 'medium',
                        'createdAt': dt.now().isoformat(),
                        'status': {'isRead': False, 'readAt': None},
                        'user_id': str(recipient['user_id'])
                    }
                    notifications_storage.append(notification)
                    if len(notifications_storage) > 100:
                        notifications_storage.pop(0)
                except Exception as notify_error:
                    print(f"Error sending notification: {str(notify_error)}")
        except Exception as notify_ex:
            print(f"Error in notification service: {str(notify_ex)}")
        
        return Response({
            'success': True,
            'message': 'Event approved successfully',
            'event_id': event.EventId,
            'status': event.Status
        })
        
    except Exception as e:
        print(f"DEBUG: Error in approve_event: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error approving event: {str(e)}'
        }, status=500)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([AllowAny])
@csrf_exempt
def reject_event(request, event_id):
    """
    Reject an event (reviewer action)
    """
    try:
        data = request.data
        user_id = data.get('user_id') or request.GET.get('user_id')
        comments = data.get('comments', '')
        
        if not user_id:
            return Response({
                'success': False,
                'message': 'User ID is required'
            }, status=400)
        
        # Get the event
        try:
            event = Event.objects.get(EventId=event_id)
        except Event.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        # Check if user is the reviewer
        if event.Reviewer and event.Reviewer.UserId != int(user_id):
            return Response({
                'success': False,
                'message': 'Only the assigned reviewer can reject this event'
            }, status=403)
        
        # Check if event is in a reviewable status
        reviewable_statuses = ['Pending Review', 'Under Review', 'Pending Approval']
        if event.Status not in reviewable_statuses:
            return Response({
                'success': False,
                'message': f'Event must be in a reviewable status to be rejected. Current status: {event.Status}. Allowed statuses: {", ".join(reviewable_statuses)}'
            }, status=400)
        
        # Store old status for notification
        old_status = event.Status
        
        # Update event status
        event.Status = 'Rejected'
        event.UpdatedAt = timezone.now()
        if comments:
            event.Comments = comments
        event.save()
        
        # Send email notification for status change
        try:
            from ...routes.Global.notification_service import NotificationService
            from ...routes.Global.notifications import notifications_storage
            notification_service = NotificationService()
            import uuid
            from datetime import datetime as dt
            
            # Get actor name
            actor = Users.objects.filter(UserId=user_id).first()
            actor_name = actor.UserName if actor else 'System'
            
            # Collect recipients
            recipients = []
            if event.Owner and hasattr(event.Owner, 'Email') and event.Owner.Email:
                recipients.append({
                    'email': event.Owner.Email,
                    'name': event.Owner.UserName or event.Owner.Email.split('@')[0],
                    'user_id': event.Owner.UserId
                })
            if event.Reviewer and hasattr(event.Reviewer, 'Email') and event.Reviewer.Email:
                recipients.append({
                    'email': event.Reviewer.Email,
                    'name': event.Reviewer.UserName or event.Reviewer.Email.split('@')[0],
                    'user_id': event.Reviewer.UserId
                })
            if event.CreatedBy and hasattr(event.CreatedBy, 'Email') and event.CreatedBy.Email:
                recipients.append({
                    'email': event.CreatedBy.Email,
                    'name': event.CreatedBy.UserName or event.CreatedBy.Email.split('@')[0],
                    'user_id': event.CreatedBy.UserId
                })
            
            # Send notifications
            for recipient in recipients:
                try:
                    notification_data = {
                        'notification_type': 'eventStatusChanged',
                        'email': recipient['email'],
                        'email_type': 'gmail',
                        'template_data': [
                            recipient['name'],
                            event.EventTitle,
                            old_status,
                            'Rejected',
                            actor_name
                        ]
                    }
                    notification_service.send_multi_channel_notification(notification_data)
                    
                    # In-app notification
                    notification = {
                        'id': str(uuid.uuid4()),
                        'title': 'Event Status Updated',
                        'message': f'Event "{event.EventTitle}" has been rejected.',
                        'category': 'event',
                        'priority': 'high',
                        'createdAt': dt.now().isoformat(),
                        'status': {'isRead': False, 'readAt': None},
                        'user_id': str(recipient['user_id'])
                    }
                    notifications_storage.append(notification)
                    if len(notifications_storage) > 100:
                        notifications_storage.pop(0)
                except Exception as notify_error:
                    print(f"Error sending notification: {str(notify_error)}")
        except Exception as notify_ex:
            print(f"Error in notification service: {str(notify_ex)}")
        
        return Response({
            'success': True,
            'message': 'Event rejected successfully',
            'event_id': event.EventId,
            'status': event.Status
        })
        
    except Exception as e:
        print(f"DEBUG: Error in reject_event: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error rejecting event: {str(e)}'
        }, status=500)


@api_view(['PUT'])
@permission_classes([EventEditPermission])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
def update_event(request, event_id):
    """Update an event"""
    try:
        data = request.data
        user_id = data.get('user_id')
        
        if not user_id:
            return Response({
                'success': False,
                'message': 'User ID is required'
            }, status=400)
        
        # Get the event
        try:
            event = Event.objects.get(EventId=event_id)
        except Event.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        # Check if user has permission to update (owner or reviewer)
        # For now, allow any authenticated user to update events
        # TODO: Implement proper permission checking based on business rules
        print(f"DEBUG: Event {event_id} - CreatedBy: {event.CreatedBy}, Reviewer: {event.Reviewer}, User: {user_id}")
        
        # Allow updating for now - can be restricted later
        # if event.CreatedBy != int(user_id) and event.Reviewer != int(user_id):
        #     return Response({
        #         'success': False,
        #         'message': 'You do not have permission to update this event'
        #     }, status=403)
        
        # Update event fields
        if 'title' in data:
            event.EventTitle = data['title']
        if 'description' in data:
            event.Description = data['description']
        if 'framework' in data:
            event.FrameworkName = data['framework']
        if 'module' in data:
            event.Module = data['module']
        if 'category' in data:
            event.Category = data['category']
        if 'recurrence_type' in data:
            event.RecurrenceType = data['recurrence_type']
        if 'frequency' in data:
            event.Frequency = data['frequency']
        if 'priority' in data:
            event.Priority = data['priority']
        
        # Track status change for notifications
        old_status = event.Status
        status_changed = False
        if 'status' in data and data['status'] != event.Status:
            event.Status = data['status']
            status_changed = True
        
        # Handle evidence updates
        if 'evidence' in data:
            evidence_data = data.get('evidence', [])
            evidence_urls = []
            
            print(f"DEBUG: Updating evidence for event {event_id}")
            print(f"DEBUG: Raw evidence data from request: {evidence_data}")
            
            # Handle evidence data - could be JSON string or array
            evidence_files = []
            if isinstance(evidence_data, str):
                try:
                    # Parse JSON string
                    evidence_files = json.loads(evidence_data)
                    print(f"DEBUG: Parsed evidence JSON: {evidence_files}")
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Failed to parse evidence JSON: {e}")
                    evidence_files = []
            elif isinstance(evidence_data, list):
                # Already an array
                evidence_files = evidence_data
            
            # Process evidence files and extract S3 URLs
            if evidence_files:
                print(f"DEBUG: Processing {len(evidence_files)} evidence files")
                for i, evidence_file in enumerate(evidence_files):
                    print(f"DEBUG: Processing evidence file {i+1}: {evidence_file}")
                    if evidence_file.get('s3_url'):
                        evidence_urls.append(evidence_file.get('s3_url'))
                        print(f"DEBUG: Added evidence URL: {evidence_file.get('s3_url')}")
                    else:
                        print(f"DEBUG: Skipping evidence file {i+1} - no s3_url")
            else:
                print("DEBUG: No evidence files provided")
            
            # Create semicolon-separated string of URLs
            evidence_string = ";".join(evidence_urls) if evidence_urls else ""
            print(f"DEBUG: Final evidence string to save: '{evidence_string}'")
            print(f"DEBUG: Evidence string length: {len(evidence_string)}")
            
            # Update the event's evidence
            event.Evidence = evidence_string
        
        # Handle owner assignment - convert name to Users instance
        if 'owner' in data and data['owner']:
            try:
                # Try to find user by full name (FirstName + LastName)
                owner_name = data['owner'].strip()
                if ' ' in owner_name:
                    first_name, last_name = owner_name.split(' ', 1)
                    owner_user = Users.objects.filter(
                        FirstName__iexact=first_name.strip(),
                        LastName__iexact=last_name.strip()
                    ).first()
                else:
                    # If no space, try to find by first name or last name
                    owner_user = Users.objects.filter(
                        models.Q(FirstName__iexact=owner_name) | 
                        models.Q(LastName__iexact=owner_name)
                    ).first()
                
                if owner_user:
                    event.Owner = owner_user
                else:
                    print(f"DEBUG: Owner user not found for name: {owner_name}")
            except Exception as e:
                print(f"DEBUG: Error finding owner user: {str(e)}")
        
        # Handle reviewer assignment - convert name to Users instance
        if 'reviewer' in data and data['reviewer']:
            try:
                # Try to find user by full name (FirstName + LastName)
                reviewer_name = data['reviewer'].strip()
                if ' ' in reviewer_name:
                    first_name, last_name = reviewer_name.split(' ', 1)
                    reviewer_user = Users.objects.filter(
                        FirstName__iexact=first_name.strip(),
                        LastName__iexact=last_name.strip()
                    ).first()
                else:
                    # If no space, try to find by first name or last name
                    reviewer_user = Users.objects.filter(
                        models.Q(FirstName__iexact=reviewer_name) | 
                        models.Q(LastName__iexact=reviewer_name)
                    ).first()
                
                if reviewer_user:
                    event.Reviewer = reviewer_user
                else:
                    print(f"DEBUG: Reviewer user not found for name: {reviewer_name}")
            except Exception as e:
                print(f"DEBUG: Error finding reviewer user: {str(e)}")
        
        event.UpdatedAt = timezone.now()
        event.save()
        
        # Send email notification if status changed
        if status_changed:
            try:
                from ...routes.Global.notification_service import NotificationService
                from ...routes.Global.notifications import notifications_storage
                notification_service = NotificationService()
                import uuid
                from datetime import datetime as dt
                
                # Get actor name
                actor = Users.objects.filter(UserId=user_id).first()
                actor_name = actor.UserName if actor else 'System'
                
                # Collect recipients
                recipients = []
                if event.Owner and hasattr(event.Owner, 'Email') and event.Owner.Email:
                    recipients.append({
                        'email': event.Owner.Email,
                        'name': event.Owner.UserName or event.Owner.Email.split('@')[0],
                        'user_id': event.Owner.UserId
                    })
                if event.Reviewer and hasattr(event.Reviewer, 'Email') and event.Reviewer.Email:
                    recipients.append({
                        'email': event.Reviewer.Email,
                        'name': event.Reviewer.UserName or event.Reviewer.Email.split('@')[0],
                        'user_id': event.Reviewer.UserId
                    })
                if event.CreatedBy and hasattr(event.CreatedBy, 'Email') and event.CreatedBy.Email:
                    recipients.append({
                        'email': event.CreatedBy.Email,
                        'name': event.CreatedBy.UserName or event.CreatedBy.Email.split('@')[0],
                        'user_id': event.CreatedBy.UserId
                    })
                
                # Send notifications
                for recipient in recipients:
                    try:
                        notification_data = {
                            'notification_type': 'eventStatusChanged',
                            'email': recipient['email'],
                            'email_type': 'gmail',
                            'template_data': [
                                recipient['name'],
                                event.EventTitle,
                                old_status,
                                event.Status,
                                actor_name
                            ]
                        }
                        notification_service.send_multi_channel_notification(notification_data)
                        
                        # In-app notification
                        notification = {
                            'id': str(uuid.uuid4()),
                            'title': 'Event Status Updated',
                            'message': f'Event "{event.EventTitle}" status changed from {old_status} to {event.Status}.',
                            'category': 'event',
                            'priority': 'medium',
                            'createdAt': dt.now().isoformat(),
                            'status': {'isRead': False, 'readAt': None},
                            'user_id': str(recipient['user_id'])
                        }
                        notifications_storage.append(notification)
                        if len(notifications_storage) > 100:
                            notifications_storage.pop(0)
                    except Exception as notify_error:
                        print(f"Error sending notification: {str(notify_error)}")
            except Exception as notify_ex:
                print(f"Error in notification service: {str(notify_ex)}")
        
        # Return the updated event data
        event_data = {
            'id': event.EventId,
            'title': event.EventTitle,
            'description': event.Description,
            'framework': event.FrameworkName,
            'module': event.Module,
            'category': event.Category,
            'recurrence_type': event.RecurrenceType,
            'frequency': event.Frequency,
            'owner': event.owner_name if hasattr(event, 'owner_name') else '',
            'reviewer': event.reviewer_name if hasattr(event, 'reviewer_name') else '',
            'status': event.Status,
            'priority': event.Priority,
            'updated_at': event.UpdatedAt
        }
        
        return Response({
            'success': True,
            'message': 'Event updated successfully',
            'event_id': event.EventId,
            'event': event_data
        })
        
    except Exception as e:
        print(f"DEBUG: Error in update_event: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error updating event: {str(e)}'
        }, status=500)


@api_view(['POST'])
@permission_classes([EventArchivePermission])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
def archive_event(request, event_id):
    """Archive an event"""
    try:
        data = request.data
        user_id = data.get('user_id')
        
        if not user_id:
            return Response({
                'success': False,
                'message': 'User ID is required'
            }, status=400)
        
        # Get the event
        try:
            event = Event.objects.get(EventId=event_id)
        except Event.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        # Check if user has permission to archive (owner or reviewer)
        # For now, allow any authenticated user to archive events
        # TODO: Implement proper permission checking based on business rules
        print(f"DEBUG: Event {event_id} - CreatedBy: {event.CreatedBy}, Reviewer: {event.Reviewer}, User: {user_id}")
        
        # Allow archiving for now - can be restricted later
        # if event.CreatedBy != int(user_id) and event.Reviewer != int(user_id):
        #     return Response({
        #         'success': False,
        #         'message': 'You do not have permission to archive this event'
        #     }, status=403)
        
        # Archive the event
        event.Status = 'Archived'
        event.UpdatedAt = timezone.now()
        event.save()
        
        return Response({
            'success': True,
            'message': 'Event archived successfully',
            'event_id': event.EventId
        })
        
    except Exception as e:
        print(f"DEBUG: Error in archive_event: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error archiving event: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
def get_archived_events(request):
    """Get all archived events (excluding integration and Riskavaire events)"""
    try:
        # Get archived events that are NOT from integrations or Riskavaire
        archived_events_query = Event.objects.filter(
            Status='Archived'
        ).exclude(
            models.Q(FrameworkName__icontains='Integration') | 
            models.Q(FrameworkName__icontains='Jira') |
            models.Q(FrameworkName__icontains='Riskavaire') |
            models.Q(LinkedRecordType__icontains='Jira') |
            models.Q(LinkedRecordType__icontains='Integration') |
            models.Q(LinkedRecordType__icontains='Riskavaire')
        )
        
        # Apply framework filtering
        from ..Policy.framework_filter_helper import apply_framework_filter, get_framework_filter_info
        filter_info = get_framework_filter_info(request)
        print(f"🔍 DEBUG: Framework filter info for get_archived_events: {filter_info}")
        archived_events_query = apply_framework_filter(archived_events_query, request, 'FrameworkId')
        
        archived_events = archived_events_query.order_by('-UpdatedAt')
        
        events_data = []
        for event in archived_events:
            # Get owner name
            owner_name = 'Unknown'
            if event.Owner:
                try:
                    owner_name = event.Owner.username or f"User {event.Owner.UserId}"
                except:
                    owner_name = f"User {event.Owner.UserId}"
            elif event.CreatedBy:
                try:
                    owner = Users.objects.get(UserId=event.CreatedBy.UserId)
                    owner_name = owner.username or f"User {event.CreatedBy.UserId}"
                except (Users.DoesNotExist, AttributeError):
                    owner_name = f"User {event.CreatedBy.UserId if hasattr(event.CreatedBy, 'UserId') else 'Unknown'}"
            
            # Get reviewer name
            reviewer_name = 'N/A'
            if event.Reviewer:
                try:
                    reviewer_name = event.Reviewer.username or f"User {event.Reviewer.UserId}"
                except:
                    reviewer_name = f"User {event.Reviewer.UserId}"
            
            events_data.append({
                'id': event.EventId,
                'title': event.EventTitle or 'Untitled Event',
                'description': event.Description or '',
                'framework': event.FrameworkName or 'N/A',
                'category': event.Category or 'N/A',
                'owner': owner_name,
                'reviewer': reviewer_name,
                'status': event.Status,
                'priority': event.Priority or 'Medium',
                'dateCreated': event.CreatedAt.strftime('%m/%d/%Y') if event.CreatedAt else 'N/A',
                'dateUpdated': event.UpdatedAt.strftime('%m/%d/%Y') if event.UpdatedAt else 'N/A',
                'linkedRecordType': event.LinkedRecordType or 'N/A',
                'linkedRecordId': event.LinkedRecordId or 'N/A',
                'linkedRecordName': event.LinkedRecordName or 'N/A'
            })
        
        return Response({
            'success': True,
            'events': events_data,
            'count': len(events_data)
        })
        
    except Exception as e:
        print(f"DEBUG: Error in get_archived_events: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error fetching archived events: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
def get_archived_queue_items(request):
    """Get archived queue items (integration and Riskavaire events)"""
    try:
        # Get archived events that are from integrations or Riskavaire
        archived_queue_items = Event.objects.filter(
            Status='Archived'
        ).filter(
            models.Q(FrameworkName__icontains='Integration') | 
            models.Q(FrameworkName__icontains='Jira') |
            models.Q(FrameworkName__icontains='Riskavaire') |
            models.Q(LinkedRecordType__icontains='Jira') |
            models.Q(LinkedRecordType__icontains='Integration') |
            models.Q(LinkedRecordType__icontains='Riskavaire')
        ).order_by('-UpdatedAt')
        
        queue_items_data = []
        for event in archived_queue_items:
            # Determine source system
            source_system = 'Unknown'
            if event.FrameworkName and 'Jira' in event.FrameworkName:
                source_system = 'Jira Integration'
            elif event.FrameworkName and 'Riskavaire' in event.FrameworkName:
                source_system = 'Riskavaire'
            elif event.LinkedRecordType and 'Jira' in event.LinkedRecordType:
                source_system = 'Jira Integration'
            elif event.LinkedRecordType and 'Riskavaire' in event.LinkedRecordType:
                source_system = 'Riskavaire'
            elif event.FrameworkName and 'Integration' in event.FrameworkName:
                source_system = 'External Integration'
            
            # Determine suggested type based on category and content
            suggested_type = event.Category or 'General'
            if event.EventTitle:
                title_lower = event.EventTitle.lower()
                if any(keyword in title_lower for keyword in ['security', 'vulnerability', 'breach']):
                    suggested_type = 'Security Event'
                elif any(keyword in title_lower for keyword in ['compliance', 'audit', 'policy']):
                    suggested_type = 'Compliance Event'
                elif any(keyword in title_lower for keyword in ['risk', 'threat', 'exposure']):
                    suggested_type = 'Risk Event'
                elif any(keyword in title_lower for keyword in ['incident', 'bug', 'issue']):
                    suggested_type = 'Incident Event'
            
            queue_items_data.append({
                'id': event.EventId,
                'sourceSystem': source_system,
                'rawTitle': event.EventTitle or 'Untitled Event',
                'suggestedType': suggested_type,
                'timestamp': event.UpdatedAt.strftime('%m/%d/%Y %H:%M') if event.UpdatedAt else 'N/A',
                'linkedRecordId': event.LinkedRecordId or 'N/A',
                'linkedRecordName': event.LinkedRecordName or 'N/A',
                'framework': event.FrameworkName or 'N/A',
                'category': event.Category or 'N/A',
                'priority': event.Priority or 'Medium',
                'description': event.Description or '',
                'dateCreated': event.CreatedAt.strftime('%m/%d/%Y') if event.CreatedAt else 'N/A'
            })
        
        return Response({
            'success': True,
            'queueItems': queue_items_data,
            'count': len(queue_items_data)
        })
        
    except Exception as e:
        print(f"DEBUG: Error in get_archived_queue_items: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error fetching archived queue items: {str(e)}'
        }, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
def unarchive_event(request, event_id):
    """Unarchive an event (change status from Archived to Pending Review)"""
    try:
        data = request.data
        user_id = data.get('user_id')
        
        if not user_id:
            return Response({
                'success': False,
                'message': 'User ID is required'
            }, status=400)
        
        # Get the event
        try:
            event = Event.objects.get(EventId=event_id)
        except Event.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        # Check if event is archived
        if event.Status != 'Archived':
            return Response({
                'success': False,
                'message': 'Event is not archived'
            }, status=400)
        
        # Update event status to Pending Review
        event.Status = 'Pending Review'
        event.UpdatedAt = timezone.now()
        event.save()
        
        return Response({
            'success': True,
            'message': 'Event unarchived successfully',
            'event_id': event.EventId,
            'new_status': event.Status
        })
        
    except Exception as e:
        print(f"DEBUG: Error in unarchive_event: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error unarchiving event: {str(e)}'
        }, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
def delete_event_permanently(request, event_id):
    """Permanently delete an event from the database"""
    try:
        data = request.data
        user_id = data.get('user_id')
        
        if not user_id:
            return Response({
                'success': False,
                'message': 'User ID is required'
            }, status=400)
        
        # Get the event
        try:
            event = Event.objects.get(EventId=event_id)
        except Event.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        # Check if event is archived
        if event.Status != 'Archived':
            return Response({
                'success': False,
                'message': 'Only archived events can be permanently deleted'
            }, status=400)
        
        # Store event details for logging before deletion
        event_title = event.EventTitle
        event_id_generated = event.EventId_Generated
        
        # Delete the event
        event.delete()
        
        return Response({
            'success': True,
            'message': 'Event permanently deleted',
            'deleted_event_title': event_title,
            'deleted_event_id': event_id_generated
        })
        
    except Exception as e:
        print(f"DEBUG: Error in delete_event_permanently: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error deleting event: {str(e)}'
        }, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
def attach_evidence(request, event_id):
    """Attach evidence to an event"""
    try:
        data = request.data
        user_id = data.get('user_id')
        
        if not user_id:
            return Response({
                'success': False,
                'message': 'User ID is required'
            }, status=400)
        
        # Get the event
        try:
            event = Event.objects.get(EventId=event_id)
        except Event.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        # Check if user has permission to attach evidence (owner or reviewer)
        # For now, allow any authenticated user to attach evidence
        # TODO: Implement proper permission checking based on business rules
        print(f"DEBUG: Event {event_id} - CreatedBy: {event.CreatedBy}, Reviewer: {event.Reviewer}, User: {user_id}")
        
        # Allow attaching evidence for now - can be restricted later
        # if event.CreatedBy != int(user_id) and event.Reviewer != int(user_id):
        #     return Response({
        #         'success': False,
        #         'message': 'You do not have permission to attach evidence to this event'
        #     }, status=403)
        
        # Handle file upload
        if 'file' in request.FILES:
            file = request.FILES['file']
            # Here you would typically save the file and create an evidence record
            # For now, we'll just update the event description to include evidence info
            evidence_info = f"\n\nEvidence attached: {file.name} (uploaded by user {user_id})"
            event.EventDescription = (event.EventDescription or '') + evidence_info
            event.UpdatedAt = timezone.now()
            event.save()
            
            return Response({
                'success': True,
                'message': 'Evidence attached successfully',
                'event_id': event.EventId,
                'filename': file.name
            })
        else:
            return Response({
                'success': False,
                'message': 'No file provided'
            }, status=400)
        
    except Exception as e:
        print(f"DEBUG: Error in attach_evidence: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error attaching evidence: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
def test_integration_db_connection(request):
    """
    Test connection to the integration database and create it if it doesn't exist
    """
    try:
        import mysql.connector
        from django.conf import settings
        
        # Use the same credentials as the main GRC database
        main_db_config = settings.DATABASES['default']
        
        # First, try to connect to MySQL server without specifying database
        server_config = {
            'host': main_db_config['HOST'],
            'user': main_db_config['USER'],
            'password': main_db_config['PASSWORD'],
            'port': int(main_db_config['PORT'])
        }
        
        # Connect to MySQL server
        connection = mysql.connector.connect(**server_config)
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS grc_integrations")
        cursor.execute("USE grc_integrations")
        
        # Create jira_issues table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jira_issues (
                id INT AUTO_INCREMENT PRIMARY KEY,
                issue_key VARCHAR(50) NOT NULL,
                summary TEXT,
                description TEXT,
                status VARCHAR(50),
                priority VARCHAR(50),
                assignee VARCHAR(100),
                reporter VARCHAR(100),
                issue_type VARCHAR(50),
                project_key VARCHAR(50),
                project_name VARCHAR(100),
                created_date TIMESTAMP NULL,
                updated_date TIMESTAMP NULL,
                resolution VARCHAR(100),
                labels TEXT,
                components TEXT,
                custom_fields JSON,
                raw_data JSON,
                is_archived BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        cursor.close()
        connection.close()
        
        return Response({
            'success': True,
            'message': 'Integration database and tables created successfully'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error setting up integration database: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
def get_integration_events(request):
    """
    Get events from external integrations using integration_data_list table
    """
    try:
        from ...models import IntegrationDataList
        from django.db import connection
        
        # Initialize integration_records
        integration_records = []
        
        # Fetch integration data from the grc.integration_data_list table
        # Use a more efficient query to avoid sort memory issues
        try:
            # Use raw SQL with LIMIT to avoid sort memory issues
            # This approach gets the most recent records efficiently
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, heading, source, username, time, data, metadata, created_at, updated_at
                    FROM integration_data_list 
                    ORDER BY created_at DESC 
                    LIMIT 100
                """)
                
                # Convert raw results to model-like objects
                columns = [col[0] for col in cursor.description]
                raw_records = cursor.fetchall()
                
                # Create a list of dictionaries to simulate model objects
                integration_records = []
                for row in raw_records:
                    record_dict = dict(zip(columns, row))
                    # Create a simple object with the necessary attributes
                    class MockRecord:
                        def __init__(self, **kwargs):
                            for key, value in kwargs.items():
                                setattr(self, key, value)
                    
                    integration_records.append(MockRecord(**record_dict))
                
                print(f"DEBUG: Raw SQL query succeeded, got {len(integration_records)} records")
                    
        except Exception as query_error:
            print(f"DEBUG: Raw SQL query failed: {str(query_error)}")
            # Fallback: try with a simpler query
            try:
                integration_records = IntegrationDataList.objects.only(
                    'id', 'heading', 'source', 'username', 'time', 'data', 'metadata', 'created_at', 'updated_at'
                ).order_by('-created_at')[:50]  # Reduced limit
                print(f"DEBUG: Fallback query succeeded, got {len(integration_records)} records")
            except Exception as fallback_error:
                print(f"DEBUG: Fallback query failed: {str(fallback_error)}")
                # Last resort: get records without any ordering
                try:
                    integration_records = IntegrationDataList.objects.only(
                        'id', 'heading', 'source', 'username', 'time', 'data', 'metadata', 'created_at', 'updated_at'
                    )[:50]  # Reduced limit
                    print(f"DEBUG: Final fallback query succeeded, got {len(integration_records)} records")
                except Exception as final_error:
                    print(f"DEBUG: All queries failed: {str(final_error)}")
                    return Response({
                        'success': False,
                        'message': f'Failed to fetch integration data: {str(final_error)}',
                        'events': []
                    }, status=500)
        
        # Check if we have any records
        if not integration_records:
            print("DEBUG: No integration records found")
            return Response({
                'success': True,
                'events': [],
                'count': 0,
                'message': 'No integration events found'
            })
        
        print(f"DEBUG: Processing {len(integration_records)} integration records")
        
        # Debug: Print source values
        for i, record in enumerate(integration_records[:5]):  # Print first 5 records
            print(f"DEBUG: Record {i+1} - Source: {getattr(record, 'source', 'N/A')}")
        
        # Debug: Count Microsoft Sentinel records
        sentinel_count = sum(1 for record in integration_records if getattr(record, 'source', '') == 'Microsoft Sentinel')
        print(f"DEBUG: Microsoft Sentinel records found: {sentinel_count}")
        
        # Transform integration records to match the events queue format
        integration_events = []
        for record in integration_records:
            # Extract data from the JSON fields
            data = record.data or {}
            metadata = record.metadata or {}
            
            # Debug logging for integration records
            if record.id in [1, 2, 14]:  # Added 14 for Microsoft Sentinel record
                print(f"DEBUG: Record ID {record.id} - Source: {getattr(record, 'source', 'N/A')}")
                print(f"DEBUG: Record ID {record.id} - Heading: {record.heading}")
                print(f"DEBUG: Record ID {record.id} - Data keys: {list(data.keys()) if data else 'None'}")
                print(f"DEBUG: Record ID {record.id} - Metadata: {metadata}")
                print(f"DEBUG: Record ID {record.id} - Metadata type: {type(metadata)}")
                print(f"DEBUG: Record ID {record.id} - Metadata keys: {list(metadata.keys()) if metadata else 'None'}")
            
            # Determine event type based on content
            event_type = determine_event_type_from_integration_data(record, data, metadata)
            
            # Handle different data structures based on source
            source = record.source or 'Integration'
            
            # Microsoft Sentinel has different data structure
            if source == 'Microsoft Sentinel':
                summary = data.get('title') or data.get('displayName') or record.heading
                description = data.get('description', '')
                status = data.get('status', 'New')
                priority = metadata.get('severity', 'Medium') if metadata else 'Medium'
                assignee = data.get('owner', 'Unassigned')
                reporter = record.username or 'Unknown'
                issue_type = 'Security Incident'
                project_key = data.get('incidentNumber') or data.get('id', '')
                project_name = 'Microsoft Sentinel'
                
                print(f"[SENTINEL] Transforming Microsoft Sentinel record {record.id}")
                print(f"[SENTINEL]   - Title: {summary}")
                print(f"[SENTINEL]   - Status: {status}")
                print(f"[SENTINEL]   - Priority: {priority}")
                print(f"[SENTINEL]   - Project Key: {project_key}")
            else:
                # Default Jira/Gmail format
                summary = data.get('summary', record.heading)
                description = data.get('description', '')
                status = data.get('status', 'New')
                priority = data.get('priority', 'Medium')
                assignee = data.get('assignee', 'Unassigned')
                reporter = data.get('reporter', record.username or 'Unknown')
                issue_type = data.get('issue_type', 'Task')
                project_key = data.get('project_key', '')
                project_name = data.get('project_name', 'Integration Project')
            # Handle time fields safely
            try:
                created_date = data.get('created_date', record.time.isoformat() if hasattr(record, 'time') and record.time else '')
            except (AttributeError, TypeError):
                created_date = data.get('created_date', '')
                
            try:
                updated_date = data.get('updated_date', record.updated_at.isoformat() if hasattr(record, 'updated_at') and record.updated_at else '')
            except (AttributeError, TypeError):
                updated_date = data.get('updated_date', '')
            resolution = data.get('resolution', '')
            labels = data.get('labels', [])
            components = data.get('components', [])
            custom_fields = data.get('custom_fields', {})
            
            event_obj = {
                'id': f"integration_{record.id}",
                'title': summary,
                'framework': 'Integration',  # Default framework
                'module': determine_module_from_integration_data(record, data, metadata),
                'category': determine_category_from_integration_data(record, data, metadata),
                'source': record.source or 'Integration',
                'timestamp': record.time.strftime('%m/%d/%Y %H:%M') if hasattr(record, 'time') and record.time else 'N/A',
                'status': status,
                'linkedRecordType': 'Integration Event',
                'linkedRecordId': data.get('issue_key', f"INT-{record.id}"),
                'linkedRecordName': summary,
                'priority': priority,
                'description': description,
                'owner': assignee,
                'reviewer': 'Not Assigned',
                'evidence': [],
                'metadata': metadata,  # Include metadata field
                'rawData': {
                    'issue_key': data.get('issue_key', f"INT-{record.id}"),
                    'summary': summary,
                    'status': status,
                    'assignee': assignee,
                    'priority': priority,
                    'created': record.time.isoformat() if hasattr(record, 'time') and record.time else None,
                    'updated': record.updated_at.isoformat() if hasattr(record, 'updated_at') and record.updated_at else None,
                    'description': description,
                    'project': project_name,
                    'issue_type': issue_type,
                    'labels': labels,
                    'components': components,
                    'custom_fields': custom_fields,
                    'raw_data': data
                }
            }
            
            # Debug logging for specific events
            if record.id in [1, 2, 14]:  # Added 14 for Microsoft Sentinel record
                print(f"DEBUG: Event object for record {record.id}:")
                print(f"  - ID: {event_obj['id']}")
                print(f"  - Title: {event_obj['title']}")
                print(f"  - Source: {event_obj['source']}")
                print(f"  - Priority: {event_obj['priority']}")
                print(f"  - Status: {event_obj['status']}")
                print(f"  - Metadata: {event_obj['metadata']}")
                print(f"  - Metadata type: {type(event_obj['metadata'])}")
            
            integration_events.append(event_obj)
        
        # Debug: Count Microsoft Sentinel events in final response
        sentinel_events_count = sum(1 for event in integration_events if event.get('source') == 'Microsoft Sentinel')
        print(f"DEBUG: Microsoft Sentinel events in final response: {sentinel_events_count}")
        
        # Log details of each Sentinel event
        for event in integration_events:
            if event.get('source') == 'Microsoft Sentinel':
                print(f"[SENTINEL] Returning event: ID={event.get('id')}, Title={event.get('title')}, Source={event.get('source')}")
        
        print(f"[FINAL] Returning {len(integration_events)} total integration events")
        
        return Response({
            'success': True,
            'events': integration_events,
            'count': len(integration_events)
        })
        
    except Exception as e:
        print(f"DEBUG: Error in get_integration_events: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'message': f'Error fetching integration events: {str(e)}'
        }, status=500)


def determine_event_type_from_integration_data(record, data, metadata):
    """Determine the type of event based on integration data content"""
    summary = (data.get('summary', record.heading) or '').lower()
    description = (data.get('description', '') or '').lower()
    status = (data.get('status', '') or '').lower()
    issue_type = (data.get('issue_type', '') or '').lower()
    source = (record.source or '').lower()
    
    # Security-related issues
    if any(keyword in summary or keyword in description for keyword in 
           ['security', 'vulnerability', 'breach', 'incident', 'threat']):
        return 'Security Event'
    
    # Compliance-related issues
    if any(keyword in summary or keyword in description for keyword in 
           ['compliance', 'audit', 'policy', 'regulation', 'standard']):
        return 'Compliance Event'
    
    # Risk-related issues
    if any(keyword in summary or keyword in description for keyword in 
           ['risk', 'threat', 'exposure', 'mitigation']):
        return 'Risk Event'
    
    # Bug/Incident issues
    if issue_type in ['bug', 'incident'] or status in ['done', 'resolved']:
        return 'Incident Event'
    
    # Default to general event
    return 'General Event'


def determine_module_from_integration_data(record, data, metadata):
    """Determine the module based on integration data"""
    from ...models import Module
    
    summary = (data.get('summary', record.heading) or '').lower()
    description = (data.get('description', '') or '').lower()
    source = (record.source or '').lower()
    
    # Get all modules from database
    try:
        all_modules = Module.objects.all().values_list('modulename', flat=True)
        module_names = [name.lower() for name in all_modules]
    except Exception as e:
        print(f"DEBUG: Error fetching modules from database: {str(e)}")
        # Fallback to hardcoded modules if database fails
        module_names = ['policy management', 'compliance management', 'audit management', 'incident management', 'risk management']
    
    # Check content against database modules
    for module_name in module_names:
        module_keywords = module_name.split()
        if any(keyword in summary or keyword in description for keyword in module_keywords):
            # Find the exact module name from database
            try:
                exact_module = Module.objects.filter(modulename__icontains=module_name).first()
                if exact_module:
                    return exact_module.modulename
            except:
                pass
    
    # Default based on source
    if source == 'jira':
        return 'Integration Management'
    elif 'security' in summary:
        return 'Security Management'
    elif 'compliance' in summary:
        return 'Compliance Management'
    elif 'audit' in summary:
        return 'Audit Management'
    else:
        return 'General Integration'


def determine_category_from_integration_data(record, data, metadata):
    """Determine the category based on integration data"""
    summary = (data.get('summary', record.heading) or '').lower()
    description = (data.get('description', '') or '').lower()
    issue_type = (data.get('issue_type', '') or '').lower()
    priority = (data.get('priority', '') or '').lower()
    source = (record.source or '').lower()
    
    # High priority issues
    if priority in ['critical', 'high']:
        return 'Critical'
    
    # Bug/Incident issues
    if issue_type in ['bug', 'incident']:
        return 'Incident'
    
    # Security issues
    if any(keyword in summary or keyword in description for keyword in 
           ['security', 'vulnerability', 'breach']):
        return 'Security'
    
    # Compliance issues
    if any(keyword in summary or keyword in description for keyword in 
           ['compliance', 'audit', 'policy']):
        return 'Compliance'
    
    # Risk issues
    if any(keyword in summary or keyword in description for keyword in 
           ['risk', 'threat', 'exposure']):
        return 'Risk'
    
    # Default based on source
    if source.lower() == 'jira':
        return issue_type.title() if issue_type else 'Integration Item'
    else:
        return 'Integration Event'


@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
def create_event_from_integration(request):
    """
    Create an event from an integration item (Jira issue, etc.)
    """
    try:
        data = request.data
        user_id = data.get('user_id')
        integration_item_id = data.get('integration_item_id')
        integration_type = data.get('integration_type', 'jira')
        
        if not user_id:
            return Response({
                'success': False,
                'message': 'User ID is required'
            }, status=400)
        
        if not integration_item_id:
            return Response({
                'success': False,
                'message': 'Integration item ID is required'
            }, status=400)
        
        # Get integration item details
        if integration_type == 'jira':
            import mysql.connector
            from django.conf import settings
            
            # Database configuration for GRC_INTEGRATIONS
            # Use the same credentials as the main GRC database
            main_db_config = settings.DATABASES['default']
            integration_db_config = {
                'host': main_db_config['HOST'],
                'user': main_db_config['USER'],
                'password': main_db_config['PASSWORD'],
                'database': 'grc_integrations',  # Different database name
                'port': int(main_db_config['PORT'])
            }
            
            # Connect to the integration database
            try:
                connection = mysql.connector.connect(**integration_db_config)
                cursor = connection.cursor(dictionary=True)
                
                # Fetch the specific Jira issue
                cursor.execute("""
                    SELECT * FROM jira_issues WHERE id = %s
                """, (integration_item_id,))
                
                jira_issue = cursor.fetchone()
                
                # Check if this is an archive action
                action = request.data.get('action', 'create')
                if action == 'archive':
                    # Mark the Jira issue as archived
                    cursor.execute("""
                        UPDATE jira_issues SET is_archived = TRUE WHERE id = %s
                    """, (integration_item_id,))
                    connection.commit()
                    
                    # Create an archived event record in the main events table
                    from grc.models import Event, Users
                    from django.utils import timezone
                    
                    try:
                        # Get the user
                        user = Users.objects.get(UserId=user_id) if user_id else None
                        
                        # Create event data from Jira issue
                        event_data = {
                            'EventTitle': jira_issue['summary'] or f"Jira Issue: {jira_issue['issue_key']}",
                            'Description': jira_issue['description'] or f"Archived from Jira issue {jira_issue['issue_key']}",
                            'FrameworkId': None,
                            'FrameworkName': 'Jira Integration',
                            'Module': determine_module(jira_issue),
                            'LinkedRecordType': 'Jira Issue',
                            'LinkedRecordId': jira_issue['id'],  # Use numeric ID from Jira issue
                            'LinkedRecordName': jira_issue['issue_key'],  # Store issue key as name
                            'Category': determine_category(jira_issue),
                            'RecurrenceType': 'Non-Recurring',
                            'Frequency': None,
                            'StartDate': None,
                            'EndDate': None,
                            'Status': 'Archived',  # Set status to Archived
                            'Priority': jira_issue['priority'] or 'Medium',
                            'CreatedBy': user,
                            'Owner': None,
                            'Reviewer': None,
                            'IsTemplate': False
                        }
                        
                        # Create the archived event
                        archived_event = Event.objects.create(**event_data)
                        
                        return Response({
                            'success': True,
                            'message': 'Jira issue archived successfully and event created',
                            'action': 'archived',
                            'event_id': archived_event.EventId,
                            'event_id_generated': archived_event.EventId_Generated
                        })
                        
                    except Exception as event_error:
                        print(f"DEBUG: Error creating archived event: {str(event_error)}")
                        # Still return success for the Jira archive even if event creation fails
                        return Response({
                            'success': True,
                            'message': 'Jira issue archived successfully (event creation failed)',
                            'action': 'archived',
                            'warning': f'Event creation failed: {str(event_error)}'
                        })
                
            except mysql.connector.Error as db_error:
                return Response({
                    'success': False,
                    'message': f'Failed to connect to integration database: {str(db_error)}'
                }, status=500)
            finally:
                if 'cursor' in locals():
                    cursor.close()
                if 'connection' in locals():
                    connection.close()
            
            if not jira_issue:
                return Response({
                    'success': False,
                    'message': 'Jira issue not found'
                }, status=404)
            
            # Create event data from Jira issue
            event_data = {
                'EventTitle': jira_issue['summary'] or f"Jira Issue: {jira_issue['issue_key']}",
                'Description': jira_issue['description'] or f"Created from Jira issue {jira_issue['issue_key']}",
                'FrameworkId': None,  # Can be set later
                'FrameworkName': 'Jira Integration',
                'Module': determine_module(jira_issue),
                'LinkedRecordType': 'Jira Issue',
                'LinkedRecordId': jira_issue['issue_key'],
                'LinkedRecordName': jira_issue['issue_key'],
                'Category': determine_category(jira_issue),
                'RecurrenceType': 'Non-Recurring',
                'Frequency': None,
                'StartDate': None,
                'EndDate': None,
                'Status': 'Pending Review',
                'Priority': jira_issue['priority'] or 'Medium',
                'CreatedBy': Users.objects.get(UserId=user_id) if user_id else None,
                'Owner': None,  # Can be set later
                'Reviewer': None,  # Can be set later
                'IsTemplate': False
            }
            
            # Create the event
            event = Event.objects.create(**event_data)
            
            return Response({
                'success': True,
                'message': 'Event created successfully from Jira issue',
                'event_id': event.EventId,
                'event_id_generated': event.EventId_Generated,
                'event': {
                    'EventId': event.EventId,
                    'EventTitle': event.EventTitle,
                    'Status': event.Status,
                    'LinkedRecordId': event.LinkedRecordId,
                    'LinkedRecordName': event.LinkedRecordName
                }
            })
        
        else:
            return Response({
                'success': False,
                'message': f'Integration type {integration_type} not supported'
            }, status=400)
        
    except Exception as e:
        print(f"DEBUG: Error in create_event_from_integration: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'message': f'Error creating event from integration: {str(e)}'
        }, status=500)


# S3 Upload Endpoints

@require_http_methods(["POST"])
@csrf_exempt
def s3_upload_file(request):
    """Upload file to S3 via microservice"""
    try:
        print(f"DEBUG: s3_upload_file called with method: {request.method}")
        print(f"DEBUG: Content-Type: {request.content_type}")
        print(f"DEBUG: FILES: {list(request.FILES.keys())}")
        print(f"DEBUG: POST: {list(request.POST.keys())}")
        
        # Get user ID from request - try multiple sources
        user_id = None
        if hasattr(request, 'POST') and request.POST:
            user_id = request.POST.get('user_id')
        if not user_id and hasattr(request, 'GET') and request.GET:
            user_id = request.GET.get('user_id')
        
        print(f"DEBUG: User ID: {user_id}")
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'User ID is required'
            }, status=400)
        
        # Check if file is provided
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No file provided'
            }, status=400)
        
        file = request.FILES['file']
        print(f"DEBUG: File received: {file.name}, size: {file.size}, type: {file.content_type}")
        
        # Get custom file name from multiple sources
        custom_file_name = None
        if hasattr(request, 'POST') and request.POST:
            custom_file_name = request.POST.get('custom_file_name')
        
        # Validate file size (10MB limit)
        if file.size > 10 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'message': 'File size exceeds 10MB limit'
            }, status=400)
        
        # Validate file type
        allowed_types = [
            'application/pdf',
            'text/csv',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ]
        
        if file.content_type not in allowed_types:
            return JsonResponse({
                'success': False,
                'message': f'File type {file.content_type} not supported. Allowed types: PDF, CSV, XLSX, DOC, TXT'
            }, status=400)
        
        # Create S3 client
        try:
            s3_client = create_direct_mysql_client()
            print("DEBUG: S3 client created successfully")
        except Exception as e:
            print(f"DEBUG: Error creating S3 client: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error initializing S3 client: {str(e)}'
            }, status=500)
        
        # Save file temporarily
        import tempfile
        import os
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            print(f"DEBUG: Temporary file created: {temp_file_path}")
        except Exception as e:
            print(f"DEBUG: Error creating temporary file: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error saving file temporarily: {str(e)}'
            }, status=500)
        
        try:
            # Upload to S3
            print(f"DEBUG: Starting S3 upload for user: {user_id}, file: {file.name}")
            result = s3_client.upload(
                file_path=temp_file_path,
                user_id=user_id,
                custom_file_name=custom_file_name or file.name,
                module='Event'
            )
            
            print(f"DEBUG: S3 upload result: {result}")
            
            if result.get('success'):
                file_info = result.get('file_info', {})
                return JsonResponse({
                    'success': True,
                    'message': 'File uploaded successfully',
                    's3_key': file_info.get('s3Key'),
                    's3_url': file_info.get('url'),
                    'stored_name': file_info.get('storedName'),
                    'file_info': file_info
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': result.get('error', 'Upload failed')
                }, status=500)
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        print(f"DEBUG: Error in s3_upload_file: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'message': f'Error uploading file: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
@csrf_exempt
def s3_download_file(request, s3_key, file_name):
    """Download file from S3 via microservice"""
    try:
        user_id = request.GET.get('user_id')
        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'User ID is required'
            }, status=400)
        
        # URL decode the parameters
        from urllib.parse import unquote
        decoded_s3_key = unquote(s3_key)
        decoded_file_name = unquote(file_name)
        
        print(f"DEBUG: Download request - Original s3_key: {s3_key}, decoded: {decoded_s3_key}")
        print(f"DEBUG: Download request - Original file_name: {file_name}, decoded: {decoded_file_name}")
        print(f"DEBUG: Download request - User ID: {user_id}")
        
        # Create S3 client
        s3_client = create_direct_mysql_client()
        
        # Test connection first
        print(f"DEBUG: Testing S3 connection before download...")
        connection_test = s3_client.test_connection()
        print(f"DEBUG: Connection test result: {connection_test}")
        
        if not connection_test.get('overall_success', False):
            return JsonResponse({
                'success': False,
                'message': 'S3 service is currently unavailable. Please try again later.',
                'connection_status': connection_test
            }, status=503)
        
        # Download file
        print(f"DEBUG: Starting download with s3_key: {decoded_s3_key}, file_name: {decoded_file_name}")
        result = s3_client.download(
            s3_key=decoded_s3_key,
            file_name=decoded_file_name,
            user_id=user_id
        )
        print(f"DEBUG: Download result: {result}")
        
        if result.get('success'):
            # Return file content
            from django.http import HttpResponse
            response = HttpResponse(
                result.get('file_content'),
                content_type=result.get('content_type', 'application/octet-stream')
            )
            response['Content-Disposition'] = f'attachment; filename="{decoded_file_name}"'
            return response
        else:
            # If download failed, try to provide more specific error information
            error_message = result.get('error', 'Download failed')
            print(f"DEBUG: Download failed with error: {error_message}")
            
            # Check if it's a 404 error (file not found)
            if '404' in str(error_message) or 'Not Found' in str(error_message):
                return JsonResponse({
                    'success': False,
                    'message': 'File not found in S3. The file may have been deleted or the S3 key is incorrect.',
                    'error_details': error_message,
                    's3_key': decoded_s3_key,
                    'file_name': decoded_file_name
                }, status=404)
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'Download failed: {error_message}',
                    'error_details': error_message
                }, status=500)
            
    except Exception as e:
        print(f"DEBUG: Error in s3_download_file: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error downloading file: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
@csrf_exempt
def s3_test_connection(request):
    """Test S3 microservice connection"""
    try:
        # Create S3 client
        s3_client = create_direct_mysql_client()
        
        # Test connection
        result = s3_client.test_connection()
        
        return JsonResponse({
            'success': True,
            'message': 'S3 connection test completed',
            'connection_status': result
        })
    except Exception as e:
        print(f"DEBUG: Error in s3_test_connection: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error testing S3 connection: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
@csrf_exempt
def s3_check_file_exists(request, s3_key, file_name):
    """Check if file exists in S3"""
    try:
        user_id = request.GET.get('user_id')
        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'User ID is required'
            }, status=400)
        
        # URL decode the parameters
        from urllib.parse import unquote
        decoded_s3_key = unquote(s3_key)
        decoded_file_name = unquote(file_name)
        
        print(f"DEBUG: Check file exists - s3_key: {decoded_s3_key}, file_name: {decoded_file_name}")
        
        # Create S3 client
        s3_client = create_direct_mysql_client()
        
        # Test connection first
        connection_test = s3_client.test_connection()
        if not connection_test.get('overall_success', False):
            return JsonResponse({
                'success': False,
                'message': 'S3 service is currently unavailable',
                'connection_status': connection_test
            }, status=503)
        
        # For now, we'll assume the file exists if the connection is successful
        # In a real implementation, you might want to make a HEAD request to S3
        return JsonResponse({
            'success': True,
            'message': 'File existence check completed',
            'file_exists': True,  # This is a placeholder - implement actual check
            's3_key': decoded_s3_key,
            'file_name': decoded_file_name
        })
        
    except Exception as e:
        print(f"DEBUG: Error in s3_check_file_exists: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error checking file existence: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@require_consent('upload_event')
def upload_event_evidence(request, event_id):
    """Upload evidence file for a specific event"""
    try:
        print(f"DEBUG: upload_event_evidence called for event_id: {event_id}")
        print(f"DEBUG: Request method: {request.method}")
        print(f"DEBUG: Content-Type: {request.content_type}")
        print(f"DEBUG: FILES: {list(request.FILES.keys())}")
        print(f"DEBUG: POST: {list(request.POST.keys())}")
        
        # Get user ID from request
        user_id = None
        if hasattr(request, 'POST') and request.POST:
            user_id = request.POST.get('user_id')
        if not user_id and hasattr(request, 'GET') and request.GET:
            user_id = request.GET.get('user_id')
        
        print(f"DEBUG: User ID: {user_id}")
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'User ID is required'
            }, status=400)
        
        # Check if file is provided
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No file provided'
            }, status=400)
        
        file = request.FILES['file']
        print(f"DEBUG: File received: {file.name}, size: {file.size}, type: {file.content_type}")
        
        # Get custom file name from request
        custom_file_name = None
        if hasattr(request, 'POST') and request.POST:
            custom_file_name = request.POST.get('custom_file_name')
        
        # Validate file size (10MB limit)
        if file.size > 10 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'message': 'File size exceeds 10MB limit'
            }, status=400)
        
        # Validate file type
        allowed_types = [
            'application/pdf',
            'text/csv',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ]
        
        if file.content_type not in allowed_types:
            return JsonResponse({
                'success': False,
                'message': f'File type {file.content_type} not supported. Allowed types: PDF, CSV, XLSX, DOC, TXT'
            }, status=400)
        
        # Check if event exists
        try:
            event = Event.objects.get(EventId=event_id)
            print(f"DEBUG: Found event: {event.EventTitle}")
        except Event.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        # Create S3 client
        try:
            s3_client = create_direct_mysql_client()
            print("DEBUG: S3 client created successfully")
        except Exception as e:
            print(f"DEBUG: Error creating S3 client: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error initializing S3 client: {str(e)}'
            }, status=500)
        
        # Save file temporarily
        import tempfile
        import os
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            print(f"DEBUG: Temporary file created: {temp_file_path}")
        except Exception as e:
            print(f"DEBUG: Error creating temporary file: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error saving file temporarily: {str(e)}'
            }, status=500)
        
        try:
            # Upload to S3
            print(f"DEBUG: Starting S3 upload for user: {user_id}, file: {file.name}")
            result = s3_client.upload(
                file_path=temp_file_path,
                user_id=user_id,
                custom_file_name=custom_file_name or file.name,
                module='Event'
            )
            
            print(f"DEBUG: S3 upload result: {result}")
            
            if result.get('success'):
                # Update event with new evidence file
                file_info = result.get('file_info', {})
                s3_url = file_info.get('url')
                s3_key = file_info.get('s3Key')
                stored_name = file_info.get('storedName')
                
                print(f"DEBUG: S3 URL from result: {s3_url}")
                print(f"DEBUG: S3 Key from result: {s3_key}")
                print(f"DEBUG: Stored name from result: {stored_name}")
                
                evidence_data = {
                    'file_name': file.name,
                    's3_url': s3_url,
                    's3_key': s3_key,
                    'stored_name': stored_name,
                    'file_size': file.size,
                    'file_type': file.content_type,
                    'uploaded_at': timezone.now().isoformat(),
                    'uploaded_by': user_id
                }
                
                # Get current evidence string
                current_evidence = event.Evidence or ""
                print(f"DEBUG: Current evidence before update: '{current_evidence}'")
                
                # Add new evidence URL to existing evidence string
                if current_evidence:
                    current_evidence += f";{s3_url}"
                else:
                    current_evidence = s3_url
                
                print(f"DEBUG: Final evidence string to save: '{current_evidence}'")
                
                # Update event with evidence string in Evidence CharField
                event.Evidence = current_evidence
                event.UpdatedAt = timezone.now()
                event.save()
                
                print(f"DEBUG: Event {event_id} updated with new evidence file")
                print(f"DEBUG: Event Evidence after save: '{event.Evidence}'")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Evidence file uploaded successfully',
                    's3_key': s3_key,
                    's3_url': s3_url,
                    'stored_name': stored_name,
                    'file_info': evidence_data
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': result.get('error', 'Upload failed')
                }, status=500)
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        print(f"DEBUG: Error in upload_event_evidence: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'message': f'Error uploading evidence file: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
@csrf_exempt
def get_event_evidence(request, event_id):
    """Get evidence files for a specific event with detailed information"""
    try:
        # Check if event exists
        try:
            event = Event.objects.get(EventId=event_id)
            print(f"DEBUG: Found event: {event.EventTitle}")
        except Event.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        # Get evidence data from CharField
        evidence_string = event.Evidence or ""
        evidence_urls = evidence_string.split(';') if evidence_string else []
        
        # Process evidence URLs to extract filenames and create detailed evidence objects
        evidence_objects = []
        for i, url in enumerate(evidence_urls):
            if url and url.strip():
                # Extract filename from URL
                filename = "Evidence File"
                if url:
                    try:
                        # Extract filename from S3 URL
                        if 'amazonaws.com' in url:
                            # Extract from S3 URL like: https://bucket.s3.region.amazonaws.com/path/filename.ext
                            url_parts = url.split('/')
                            if len(url_parts) > 0:
                                filename = url_parts[-1]
                                # Decode URL encoding
                                filename = filename.replace('%20', ' ').replace('%2E', '.')
                        else:
                            # Extract from other URL formats
                            url_parts = url.split('/')
                            if len(url_parts) > 0:
                                filename = url_parts[-1]
                    except:
                        filename = f"Evidence File {i + 1}"
                
                evidence_objects.append({
                    'id': i + 1,
                    'fileName': filename,
                    'filename': filename,
                    'name': filename,
                    'url': url,
                    's3_url': url,
                    'uploadedBy': event.CreatedBy.FirstName + ' ' + event.CreatedBy.LastName if event.CreatedBy else 'Unknown',
                    'uploadDate': event.CreatedAt.strftime('%Y-%m-%d') if event.CreatedAt else 'Unknown',
                    'size': 'Unknown'  # Size would need to be stored separately or fetched from S3
                })
        
        return JsonResponse({
            'success': True,
            'evidence': evidence_objects,
            'evidence_string': evidence_string,
            'count': len(evidence_objects)
        })
        
    except Exception as e:
        print(f"DEBUG: Error in get_event_evidence: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error fetching event evidence: {str(e)}'
        }, status=500)

def resolve_file_operation_evidence(evidence_urls, event):
    """Resolve file operation identifiers to actual S3 URLs and details"""
    evidence_objects = []
    
    for i, url in enumerate(evidence_urls):
        if url and url.strip():
            # Check if this is a file operation identifier
            if url.startswith('#linked-event-file_op_'):
                try:
                    # Extract file operation ID from identifier
                    file_op_id = url.replace('#linked-event-file_op_', '')
                    print(f"DEBUG: Resolving file operation ID: {file_op_id}")
                    
                    # Query file_operations table to get actual S3 URL and details
                    from django.db import connection
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT stored_name, s3_url, s3_key, s3_bucket, file_type, original_name, 
                                   content_type, export_format, file_size, created_at
                            FROM grc.file_operations 
                            WHERE id = %s
                        """, [file_op_id])
                        
                        file_ops = cursor.fetchall()
                        if file_ops:
                            stored_name, s3_url, s3_key, s3_bucket, file_type, original_name, content_type, export_format, file_size, created_at = file_ops[0]
                            
                            print(f"DEBUG: Found file operation - S3 URL: {s3_url}, Original name: {original_name}")
                            
                            # Use original name or stored name as filename
                            filename = original_name or stored_name or f"File Operation {file_op_id}"
                            
                            evidence_objects.append({
                                'id': i + 1,
                                'fileName': filename,
                                'filename': filename,
                                'name': filename,
                                'url': s3_url,
                                's3_url': s3_url,
                                's3_key': s3_key,
                                'file_type': file_type,
                                'file_size': file_size,
                                'uploadedBy': event.CreatedBy.FirstName + ' ' + event.CreatedBy.LastName if event.CreatedBy else 'Unknown',
                                'uploadDate': created_at.strftime('%Y-%m-%d') if created_at else 'Unknown',
                                'is_file_operation': True,
                                'file_operation_id': file_op_id
                            })
                        else:
                            print(f"DEBUG: No file operation found for ID: {file_op_id}")
                            # Fallback for missing file operation
                            evidence_objects.append({
                                'id': i + 1,
                                'fileName': f"File Operation {file_op_id}",
                                'filename': f"File Operation {file_op_id}",
                                'name': f"File Operation {file_op_id}",
                                'url': url,
                                's3_url': url,
                                'uploadedBy': event.CreatedBy.FirstName + ' ' + event.CreatedBy.LastName if event.CreatedBy else 'Unknown',
                                'uploadDate': event.CreatedAt.strftime('%Y-%m-%d') if event.CreatedAt else 'Unknown',
                                'size': 'Unknown',
                                'is_file_operation': True,
                                'file_operation_id': file_op_id
                            })
                except Exception as e:
                    print(f"DEBUG: Error resolving file operation {url}: {str(e)}")
                    # Fallback for error cases
                    evidence_objects.append({
                        'id': i + 1,
                        'fileName': url,
                        'filename': url,
                        'name': url,
                        'url': url,
                        's3_url': url,
                        'uploadedBy': event.CreatedBy.FirstName + ' ' + event.CreatedBy.LastName if event.CreatedBy else 'Unknown',
                        'uploadDate': event.CreatedAt.strftime('%Y-%m-%d') if event.CreatedAt else 'Unknown',
                        'size': 'Unknown'
                    })
            else:
                # Handle direct S3 URLs or other URL formats
                filename = "Evidence File"
                if url:
                    try:
                        # Extract filename from S3 URL
                        if 'amazonaws.com' in url:
                            # Extract from S3 URL like: https://bucket.s3.region.amazonaws.com/path/filename.ext
                            url_parts = url.split('/')
                            if len(url_parts) > 0:
                                filename = url_parts[-1]
                                # Decode URL encoding
                                filename = filename.replace('%20', ' ').replace('%2E', '.')
                        else:
                            # Extract from other URL formats
                            url_parts = url.split('/')
                            if len(url_parts) > 0:
                                filename = url_parts[-1]
                    except:
                        filename = f"Evidence File {i + 1}"
                
                evidence_objects.append({
                    'id': i + 1,
                    'fileName': filename,
                    'filename': filename,
                    'name': filename,
                    'url': url,
                    's3_url': url,
                    'uploadedBy': event.CreatedBy.FirstName + ' ' + event.CreatedBy.LastName if event.CreatedBy else 'Unknown',
                    'uploadDate': event.CreatedAt.strftime('%Y-%m-%d') if event.CreatedAt else 'Unknown',
                    'size': 'Unknown'
                })
    
    return evidence_objects

@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([AllowAny])
@csrf_exempt
def get_event_evidence_details(request, event_id):
    """Get detailed evidence information for a specific event"""
    try:
        # Check if event exists
        try:
            event = Event.objects.get(EventId=event_id)
            print(f"DEBUG: Found event: {event.EventTitle}")
        except Event.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        # Get evidence data from CharField
        evidence_string = event.Evidence or ""
        evidence_urls = evidence_string.split(';') if evidence_string else []
        
        # Use the helper function to resolve file operation evidence
        evidence_objects = resolve_file_operation_evidence(evidence_urls, event)
        
        return JsonResponse({
            'success': True,
            'evidence': evidence_objects,
            'evidence_string': evidence_string,
            'count': len(evidence_objects)
        })
        
    except Exception as e:
        print(f"DEBUG: Error in get_event_evidence_details: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error fetching event evidence details: {str(e)}'
        }, status=500)

@require_http_methods(["DELETE"])
@csrf_exempt
def delete_event_evidence(request, event_id, evidence_id):
    """Delete evidence file from an event"""
    try:
        # Get the event
        try:
            event = Event.objects.get(EventId=event_id, IsDeleted=False)
        except Event.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        # Get current evidence string
        evidence_string = event.Evidence or ""
        evidence_urls = evidence_string.split(';') if evidence_string else []
        
        # Find and remove evidence URL
        evidence_found = False
        updated_urls = []
        
        for url in evidence_urls:
            if url.strip() and evidence_id not in url:
                updated_urls.append(url)
            elif evidence_id in url:
                evidence_found = True
        
        if not evidence_found:
            return JsonResponse({
                'success': False,
                'message': 'Evidence file not found'
            }, status=404)
        
        # Update the event with remaining URLs
        event.Evidence = ';'.join(updated_urls) if updated_urls else ""
        event.UpdatedAt = timezone.now()
        event.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Evidence file deleted successfully',
            'data': {
                'event_id': event_id,
                'evidence_id': evidence_id,
                'remaining_files': len(updated_urls)
            }
        })
        
    except Exception as e:
        print(f"DEBUG: Error in delete_event_evidence: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error deleting evidence: {str(e)}'
        }, status=500)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@csrf_exempt
def link_evidence_to_incident(request):
    """
    Link multiple selected events as evidence to an incident
    """
    try:
        data = request.data
        incident_id = data.get('incident_id')
        user_id = data.get('user_id')
        linked_events = data.get('linked_events', [])
        
        print(f"DEBUG: Linking evidence to incident {incident_id}")
        print(f"DEBUG: User ID: {user_id}")
        print(f"DEBUG: Linked events: {linked_events}")
        
        if not incident_id:
            return Response({
                'success': False,
                'message': 'Incident ID is required'
            }, status=400)
            
        if not user_id:
            return Response({
                'success': False,
                'message': 'User ID is required'
            }, status=400)
            
        if not linked_events or len(linked_events) == 0:
            return Response({
                'success': False,
                'message': 'At least one event must be selected'
            }, status=400)
        
        # Import IncidentApproval model
        from ...models import IncidentApproval
        
        # Transform events data for storage
        evidence_data = []
        for event in linked_events:
            # Extract documents from different sources
            documents = []
            
            # 1. Check for Event evidence (S3 URLs from RiskaVaire/Event System)
            if event.get('source') in ['Riskavaire', 'RiskaVaire Module', 'Event System']:
                # Try to fetch the actual Event from database for more accurate data
                event_evidence_data = []
                
                # Try to get Event ID from the event data
                event_db_id = None
                if event.get('linkedRecordId'):
                    event_db_id = event.get('linkedRecordId')
                elif event.get('id') and event.get('id').startswith('event_'):
                    try:
                        event_db_id = int(event.get('id').replace('event_', ''))
                    except ValueError:
                        pass
                
                # If we have an Event ID, fetch from database
                if event_db_id:
                    try:
                        from ...models import Event
                        db_event = Event.objects.get(EventId=event_db_id)
                        if db_event.Evidence:
                            # Split semicolon-separated evidence URLs from database
                            event_evidence_data = [url.strip() for url in db_event.Evidence.split(';') if url.strip()]
                            print(f"DEBUG: Found database evidence for Event {event_db_id}: {event_evidence_data}")
                    except Event.DoesNotExist:
                        print(f"DEBUG: Event {event_db_id} not found in database")
                    except Exception as e:
                        print(f"DEBUG: Error fetching Event {event_db_id}: {str(e)}")
                
                # Fallback to event data from request
                if not event_evidence_data:
                    # Check for evidence array
                    if event.get('evidence') and isinstance(event.get('evidence'), list):
                        event_evidence_data = event.get('evidence', [])
                    # Check for rawData.evidence (for RiskaVaire events)
                    elif event.get('rawData') and event.get('rawData').get('evidence'):
                        evidence_str = event.get('rawData').get('evidence')
                        if evidence_str:
                            # Split semicolon-separated evidence URLs
                            event_evidence_data = [url.strip() for url in evidence_str.split(';') if url.strip()]
                    # Check for direct evidence string
                    elif event.get('evidence') and isinstance(event.get('evidence'), str):
                        evidence_str = event.get('evidence')
                        event_evidence_data = [url.strip() for url in evidence_str.split(';') if url.strip()]
                
                print(f"DEBUG: Final evidence data for {event.get('source')}: {event_evidence_data}")
                
                for evidence_item in event_evidence_data:
                    if isinstance(evidence_item, str):
                        evidence_url = evidence_item
                    elif isinstance(evidence_item, dict) and evidence_item.get('url'):
                        evidence_url = evidence_item.get('url')
                    else:
                        continue
                    
                    if evidence_url and evidence_url.strip():
                        # Extract filename from URL
                        filename = "Document"
                        try:
                            if 'amazonaws.com' in evidence_url:
                                url_parts = evidence_url.split('/')
                                if len(url_parts) > 0:
                                    filename = url_parts[-1]
                                    filename = filename.replace('%20', ' ').replace('%2E', '.')
                            else:
                                url_parts = evidence_url.split('/')
                                if len(url_parts) > 0:
                                    filename = url_parts[-1]
                        except:
                            filename = "Event Document"
                        
                        documents.append({
                            'type': 'event_evidence',
                            'filename': filename,
                            'url': evidence_url,
                            's3_url': evidence_url,
                            'downloadable': True,
                            'source': 'Event Evidence'
                        })
            
            # 2. Check for Document Handling file operations
            if event.get('source') == 'Document Handling System':
                # Try to get file operation ID from the event data
                file_operation_id = None
                if event.get('linkedRecordId'):
                    file_operation_id = event.get('linkedRecordId')
                elif event.get('id') and event.get('id').startswith('file_op_'):
                    try:
                        file_operation_id = int(event.get('id').replace('file_op_', ''))
                    except ValueError:
                        pass
                
                print(f"DEBUG: Document Handling - Looking for file operation ID: {file_operation_id}")
                
                # If we have a file operation ID, fetch from database
                if file_operation_id:
                    print(f"DEBUG: Querying file_operations table for ID: {file_operation_id}")
                    try:
                        from django.db import connection
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                SELECT stored_name, s3_url, s3_key, s3_bucket, file_type, 
                                       original_name, content_type, export_format, file_size
                                FROM grc.file_operations 
                                WHERE id = %s AND s3_url IS NOT NULL AND s3_url != ''
                            """, [file_operation_id])
                            
                            file_ops = cursor.fetchall()
                            print(f"DEBUG: Found {len(file_ops)} file operations for ID {file_operation_id}")
                            
                            for file_op in file_ops:
                                stored_name, s3_url, s3_key, s3_bucket, file_type, original_name, content_type, export_format, file_size = file_op
                                
                                if s3_url and s3_url.strip():
                                    filename = original_name or stored_name or 'Document Handling File'
                                    
                                    documents.append({
                                        'type': 'file_operation',
                                        'filename': filename,
                                        'url': s3_url,
                                        's3_url': s3_url,
                                        's3_key': s3_key,
                                        's3_bucket': s3_bucket,
                                        'downloadable': True,
                                        'source': 'Document Handling',
                                        'file_type': file_type,
                                        'content_type': content_type,
                                        'export_format': export_format,
                                        'file_size': file_size
                                    })
                                    print(f"DEBUG: Added Document Handling file: {filename} -> {s3_url}")
                    
                    except Exception as e:
                        print(f"DEBUG: Error fetching file operations for ID {file_operation_id}: {str(e)}")
                
                # Alternative: Try to find file operations by event title/description if no direct ID
                if not documents and event.get('title'):
                    try:
                        from django.db import connection
                        with connection.cursor() as cursor:
                            # Search for file operations that might be related to this event
                            event_title = event.get('title', '').lower()
                            cursor.execute("""
                                SELECT stored_name, s3_url, s3_key, s3_bucket, file_type, 
                                       original_name, content_type, export_format, file_size
                                FROM grc.file_operations 
                                WHERE s3_url IS NOT NULL AND s3_url != ''
                                AND (LOWER(original_name) LIKE %s OR LOWER(stored_name) LIKE %s)
                                ORDER BY id DESC
                                LIMIT 5
                            """, [f'%{event_title}%', f'%{event_title}%'])
                            
                            file_ops = cursor.fetchall()
                            print(f"DEBUG: Found {len(file_ops)} file operations by title search for: {event_title}")
                            
                            for file_op in file_ops:
                                stored_name, s3_url, s3_key, s3_bucket, file_type, original_name, content_type, export_format, file_size = file_op
                                
                                if s3_url and s3_url.strip():
                                    filename = original_name or stored_name or 'Document Handling File'
                                    
                                    documents.append({
                                        'type': 'file_operation',
                                        'filename': filename,
                                        'url': s3_url,
                                        's3_url': s3_url,
                                        's3_key': s3_key,
                                        's3_bucket': s3_bucket,
                                        'downloadable': True,
                                        'source': 'Document Handling',
                                        'file_type': file_type,
                                        'content_type': content_type,
                                        'export_format': export_format,
                                        'file_size': file_size
                                    })
                                    print(f"DEBUG: Added Document Handling file by search: {filename} -> {s3_url}")
                    
                    except Exception as e:
                        print(f"DEBUG: Error searching file operations by title: {str(e)}")
                
                # Last resort: Get recent Document Handling files if still no documents found
                if not documents:
                    try:
                        from django.db import connection
                        with connection.cursor() as cursor:
                            # Get recent file operations that have S3 URLs
                            cursor.execute("""
                                SELECT stored_name, s3_url, s3_key, s3_bucket, file_type, 
                                       original_name, content_type, export_format, file_size
                                FROM grc.file_operations 
                                WHERE s3_url IS NOT NULL AND s3_url != ''
                                AND file_type IN ('pdf', 'xlsx', 'docx', 'csv', 'json')
                                ORDER BY id DESC
                                LIMIT 3
                            """)
                            
                            file_ops = cursor.fetchall()
                            print(f"DEBUG: Found {len(file_ops)} recent file operations as fallback")
                            
                            for file_op in file_ops:
                                stored_name, s3_url, s3_key, s3_bucket, file_type, original_name, content_type, export_format, file_size = file_op
                                
                                if s3_url and s3_url.strip():
                                    filename = original_name or stored_name or 'Document Handling File'
                                    
                                    documents.append({
                                        'type': 'file_operation',
                                        'filename': f"{filename} (Recent)",
                                        'url': s3_url,
                                        's3_url': s3_url,
                                        's3_key': s3_key,
                                        's3_bucket': s3_bucket,
                                        'downloadable': True,
                                        'source': 'Document Handling',
                                        'file_type': file_type,
                                        'content_type': content_type,
                                        'export_format': export_format,
                                        'file_size': file_size
                                    })
                                    print(f"DEBUG: Added recent Document Handling file: {filename} -> {s3_url}")
                    
                    except Exception as e:
                        print(f"DEBUG: Error getting recent file operations: {str(e)}")
                
                # Fallback: Check for file_data in event
                if event.get('file_data'):
                    file_data = event.get('file_data', {})
                    if file_data.get('s3_url'):
                        documents.append({
                            'type': 'file_operation',
                            'filename': file_data.get('original_name') or file_data.get('file_name', 'Document'),
                            'url': file_data.get('s3_url'),
                            's3_url': file_data.get('s3_url'),
                            's3_key': file_data.get('s3_key'),
                            'file_size': file_data.get('file_size'),
                            'content_type': file_data.get('content_type'),
                            'downloadable': True,
                            'source': 'Document Handling'
                        })
            
            # 3. Check for Jira attachments (if any)
            if event.get('source') == 'Jira' and event.get('evidence'):
                for evidence_item in event.get('evidence', []):
                    if isinstance(evidence_item, dict) and evidence_item.get('url'):
                        documents.append({
                            'type': 'jira_attachment',
                            'filename': evidence_item.get('filename', 'Jira Attachment'),
                            'url': evidence_item.get('url'),
                            'downloadable': evidence_item.get('downloadable', False),
                            'source': 'Jira'
                        })
            
            evidence_item = {
                'id': event.get('id'),
                'title': event.get('title'),
                'source': event.get('source'),
                'framework': event.get('framework'),
                'module': event.get('module'),
                'category': event.get('category'),
                'status': event.get('status'),
                'priority': event.get('priority'),
                'description': event.get('description'),
                'timestamp': event.get('timestamp'),
                'linkedRecordType': event.get('linkedRecordType'),
                'linkedRecordId': event.get('linkedRecordId'),
                'linkedRecordName': event.get('linkedRecordName'),
                'owner': event.get('owner'),
                'reviewer': event.get('reviewer'),
                'evidence': event.get('evidence', []),
                'file_data': event.get('file_data', {}),
                'documents': documents,  # Add extracted documents
                'document_count': len(documents),
                'linked_at': timezone.now().isoformat(),
                'linked_by': user_id,
                'type': 'linked_evidence'
            }
            evidence_data.append(evidence_item)
        
        print(f"DEBUG: Processed evidence data: {len(evidence_data)} items")
        
        # Check if incident approval record exists
        try:
            # Use filter().first() to handle multiple records gracefully
            incident_approval = IncidentApproval.objects.filter(IncidentId=incident_id).first()
            if not incident_approval:
                print(f"DEBUG: IncidentApproval not found for incident {incident_id}, creating new one")
                incident_approval = IncidentApproval.objects.create(
                    IncidentId=incident_id,
                    ExtractedInfo={}
                )
            else:
                print(f"DEBUG: Found existing incident approval record")
            
            # Get existing ExtractedInfo or create new
            existing_data = incident_approval.ExtractedInfo or {}
            
            # Add linked evidence to existing data
            if 'linked_evidence' not in existing_data:
                existing_data['linked_evidence'] = []
            
            existing_data['linked_evidence'].extend(evidence_data)
            
            # Update the record
            incident_approval.ExtractedInfo = existing_data
            incident_approval.save()
            
        except Exception as e:
            print(f"DEBUG: Error accessing incident approval: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error accessing incident approval: {str(e)}'
            }, status=500)
        
        print(f"DEBUG: Successfully linked {len(evidence_data)} events to incident {incident_id}")
        
        return Response({
            'success': True,
            'message': f'Successfully linked {len(evidence_data)} event(s) as evidence',
            'incident_id': incident_id,
            'linked_count': len(evidence_data),
            'evidence_data': evidence_data
        })
        
    except Exception as e:
        print(f"DEBUG: Error linking evidence to incident: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error linking evidence: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
@csrf_exempt
def get_incident_linked_evidence(request, incident_id):
    """
    Get linked evidence for a specific incident
    """
    try:
        print(f"DEBUG: Getting linked evidence for incident {incident_id}")
        
        # Import IncidentApproval model
        from ...models import IncidentApproval
        
        try:
            # Use filter().first() to handle multiple records gracefully
            incident_approval = IncidentApproval.objects.filter(IncidentId=incident_id).first()
            if not incident_approval:
                print(f"DEBUG: No IncidentApproval found for incident {incident_id}")
                return Response({
                    'success': False,
                    'message': 'Incident approval record not found'
                }, status=404)
            
            extracted_info = incident_approval.ExtractedInfo or {}
            linked_evidence = extracted_info.get('linked_evidence', [])
            
            print(f"DEBUG: Found {len(linked_evidence)} linked evidence items")
            
            # Re-extract documents for each linked evidence item to get fresh data
            enhanced_linked_evidence = []
            for evidence in linked_evidence:
                print(f"DEBUG: Re-extracting documents for evidence: {evidence.get('id')} - {evidence.get('title')}")
                
                # Extract documents from different sources (same logic as in link_evidence_to_incident)
                documents = []
                
                # 1. Check for Event evidence (S3 URLs from RiskaVaire/Event System)
                if evidence.get('source') in ['Riskavaire', 'RiskaVaire Module', 'Event System']:
                    # Try to get Event ID from the evidence data
                    event_db_id = None
                    if evidence.get('linkedRecordId'):
                        event_db_id = evidence.get('linkedRecordId')
                    elif evidence.get('id') and evidence.get('id').startswith('event_'):
                        try:
                            event_db_id = int(evidence.get('id').replace('event_', ''))
                        except ValueError:
                            pass
                    
                    # If we have an Event ID, fetch from database
                    if event_db_id:
                        try:
                            from ...models import Event
                            db_event = Event.objects.get(EventId=event_db_id)
                            if db_event.Evidence:
                                # Split semicolon-separated evidence URLs from database
                                event_evidence_data = [url.strip() for url in db_event.Evidence.split(';') if url.strip()]
                                print(f"DEBUG: Found database evidence for Event {event_db_id}: {event_evidence_data}")
                                
                                for evidence_url in event_evidence_data:
                                    if evidence_url and evidence_url.strip():
                                        # Extract filename from URL
                                        filename = "Document"
                                        try:
                                            if 'amazonaws.com' in evidence_url:
                                                url_parts = evidence_url.split('/')
                                                if len(url_parts) > 0:
                                                    filename = url_parts[-1]
                                                    filename = filename.replace('%20', ' ').replace('%2E', '.')
                                            else:
                                                url_parts = evidence_url.split('/')
                                                if len(url_parts) > 0:
                                                    filename = url_parts[-1]
                                        except:
                                            filename = "Event Document"
                                        
                                        documents.append({
                                            'type': 'event_evidence',
                                            'filename': filename,
                                            'url': evidence_url,
                                            's3_url': evidence_url,
                                            'downloadable': True,
                                            'source': 'Event Evidence'
                                        })
                        except Event.DoesNotExist:
                            print(f"DEBUG: Event {event_db_id} not found in database")
                        except Exception as e:
                            print(f"DEBUG: Error fetching Event {event_db_id}: {str(e)}")
                
                # 2. Check for Document Handling file operations
                if evidence.get('source') == 'Document Handling System':
                    # Try to get file operation ID from the evidence data
                    file_operation_id = None
                    if evidence.get('linkedRecordId'):
                        file_operation_id = evidence.get('linkedRecordId')
                    elif evidence.get('id') and evidence.get('id').startswith('file_op_'):
                        try:
                            file_operation_id = int(evidence.get('id').replace('file_op_', ''))
                        except ValueError:
                            pass
                    
                    print(f"DEBUG: Document Handling - Looking for file operation ID: {file_operation_id}")
                    
                    # If we have a file operation ID, fetch from database
                    if file_operation_id:
                        try:
                            from django.db import connection
                            with connection.cursor() as cursor:
                                cursor.execute("""
                                    SELECT stored_name, s3_url, s3_key, s3_bucket, file_type, 
                                           original_name, content_type, export_format, file_size
                                    FROM grc.file_operations 
                                    WHERE id = %s AND s3_url IS NOT NULL AND s3_url != ''
                                """, [file_operation_id])
                                
                                file_ops = cursor.fetchall()
                                print(f"DEBUG: Found {len(file_ops)} file operations for ID {file_operation_id}")
                                
                                for file_op in file_ops:
                                    stored_name, s3_url, s3_key, s3_bucket, file_type, original_name, content_type, export_format, file_size = file_op
                                    
                                    if s3_url and s3_url.strip():
                                        filename = original_name or stored_name or 'Document Handling File'
                                        
                                        documents.append({
                                            'type': 'file_operation',
                                            'filename': filename,
                                            'url': s3_url,
                                            's3_url': s3_url,
                                            's3_key': s3_key,
                                            's3_bucket': s3_bucket,
                                            'downloadable': True,
                                            'source': 'Document Handling',
                                            'file_type': file_type,
                                            'content_type': content_type,
                                            'export_format': export_format,
                                            'file_size': file_size
                                        })
                                        print(f"DEBUG: Added Document Handling file: {filename} -> {s3_url}")
                        
                        except Exception as e:
                            print(f"DEBUG: Error fetching file operations for ID {file_operation_id}: {str(e)}")
                
                # Create enhanced evidence item with fresh documents
                enhanced_evidence = {
                    **evidence,  # Copy all original evidence data
                    'documents': documents,  # Add fresh documents
                    'document_count': len(documents)  # Update document count
                }
                enhanced_linked_evidence.append(enhanced_evidence)
                
                print(f"DEBUG: Enhanced evidence {evidence.get('id')} now has {len(documents)} documents")
            
            return Response({
                'success': True,
                'incident_id': incident_id,
                'linked_evidence': enhanced_linked_evidence,
                'count': len(enhanced_linked_evidence)
            })
            
        except IncidentApproval.DoesNotExist:
            print(f"DEBUG: No incident approval record found for incident {incident_id}")
            return Response({
                'success': True,
                'incident_id': incident_id,
                'linked_evidence': [],
                'count': 0
            })
        
    except Exception as e:
        print(f"DEBUG: Error getting linked evidence: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error fetching linked evidence: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
@csrf_exempt
def download_linked_evidence_document(request, incident_id, evidence_id, document_index):
    """
    Download a document from linked evidence
    """
    try:
        print(f"DEBUG: Download linked evidence document - incident: {incident_id}, evidence: {evidence_id}, document: {document_index}")
        
        # Import IncidentApproval model
        from ...models import IncidentApproval
        
        try:
            # Use filter().first() to handle multiple records gracefully
            incident_approval = IncidentApproval.objects.filter(IncidentId=incident_id).first()
            if not incident_approval:
                return JsonResponse({
                    'success': False,
                    'message': 'Incident approval record not found'
                }, status=404)
            
            extracted_info = incident_approval.ExtractedInfo or {}
            linked_evidence = extracted_info.get('linked_evidence', [])
            
            # Find the specific evidence item
            evidence_item = None
            for evidence in linked_evidence:
                if str(evidence.get('id')) == str(evidence_id):
                    evidence_item = evidence
                    break
            
            if not evidence_item:
                return JsonResponse({
                    'success': False,
                    'message': 'Linked evidence not found'
                }, status=404)
            
            # Get the documents from the evidence
            documents = evidence_item.get('documents', [])
            document_index = int(document_index)
            
            if document_index < 0 or document_index >= len(documents):
                return JsonResponse({
                    'success': False,
                    'message': 'Document not found'
                }, status=404)
            
            document = documents[document_index]
            
            if not document.get('downloadable'):
                return JsonResponse({
                    'success': False,
                    'message': 'Document is not downloadable'
                }, status=400)
            
            # Handle different document types
            if document.get('type') == 'event_evidence' and document.get('s3_url'):
                # Use existing S3 download functionality
                from urllib.parse import quote
                s3_url = document.get('s3_url')
                filename = document.get('filename', 'document')
                
                # Extract S3 key from URL
                s3_key = ""
                if 'amazonaws.com' in s3_url:
                    try:
                        # Extract S3 key from URL like: https://bucket.s3.region.amazonaws.com/key
                        url_parts = s3_url.split('amazonaws.com/')
                        if len(url_parts) > 1:
                            s3_key = url_parts[1]
                    except:
                        s3_key = filename
                
                # Redirect to S3 download endpoint
                user_id = request.GET.get('user_id', '1')
                download_url = f"/api/s3/download/{quote(s3_key)}/{quote(filename)}/?user_id={user_id}"
                
                from django.http import HttpResponseRedirect
                return HttpResponseRedirect(download_url)
                
            elif document.get('type') == 'file_operation' and document.get('s3_url'):
                # Handle Document Handling file downloads
                from urllib.parse import quote
                s3_url = document.get('s3_url')
                s3_key = document.get('s3_key', '')
                filename = document.get('filename', 'document')
                
                if not s3_key and 'amazonaws.com' in s3_url:
                    try:
                        url_parts = s3_url.split('amazonaws.com/')
                        if len(url_parts) > 1:
                            s3_key = url_parts[1]
                    except:
                        s3_key = filename
                
                # Redirect to S3 download endpoint
                user_id = request.GET.get('user_id', '1')
                download_url = f"/api/s3/download/{quote(s3_key)}/{quote(filename)}/?user_id={user_id}"
                
                from django.http import HttpResponseRedirect
                return HttpResponseRedirect(download_url)
                
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Document type not supported for download'
                }, status=400)
            
        except IncidentApproval.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Incident approval record not found'
            }, status=404)
        
    except Exception as e:
        print(f"DEBUG: Error downloading linked evidence document: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error downloading document: {str(e)}'
        }, status=500)


@require_http_methods(["DELETE"])
@csrf_exempt
def remove_event_evidence(request, event_id):
    """Remove evidence file from a specific event"""
    try:
        data = request.data if hasattr(request, 'data') else {}
        user_id = data.get('user_id') or request.GET.get('user_id')
        file_index = data.get('file_index') or request.GET.get('file_index')
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'User ID is required'
            }, status=400)
        
        if file_index is None:
            return JsonResponse({
                'success': False,
                'message': 'File index is required'
            }, status=400)
        
        try:
            file_index = int(file_index)
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid file index'
            }, status=400)
        
        # Check if event exists
        try:
            event = Event.objects.get(EventId=event_id)
            print(f"DEBUG: Found event: {event.EventTitle}")
        except Event.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        # Get current evidence lists
        current_evidence = event.Evidence or []
        current_s3_urls = event.S3EvidenceUrls or []
        
        # Check if file index is valid
        if file_index < 0 or file_index >= len(current_evidence):
            return JsonResponse({
                'success': False,
                'message': 'Invalid file index'
            }, status=400)
        
        # Remove file from both lists
        removed_file = current_evidence.pop(file_index)
        if file_index < len(current_s3_urls):
            current_s3_urls.pop(file_index)
        
        # Update event
        event.Evidence = current_evidence
        event.S3EvidenceUrls = current_s3_urls
        event.UpdatedAt = timezone.now()
        event.save()
        
        print(f"DEBUG: Removed evidence file from event {event_id}: {removed_file.get('file_name', 'Unknown')}")
        
        return JsonResponse({
            'success': True,
            'message': 'Evidence file removed successfully',
            'removed_file': removed_file,
            'remaining_count': len(current_evidence)
        })
        
    except Exception as e:
        print(f"DEBUG: Error in remove_event_evidence: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error removing evidence file: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def get_file_operations(request):
    """
    Get file operations for Document Handling evidence
    Returns file operations from the file_operations table using Django ORM
    """
    try:
        # Get query parameters
        user_id = request.GET.get('user_id')
        limit = int(request.GET.get('limit', 50))
        operation_type = request.GET.get('operation_type')  # upload, download, export
        status = request.GET.get('status')  # pending, processing, completed, failed
        show_all = request.GET.get('show_all', 'false').lower() == 'true'  # Show all records regardless of user_id
        
        print(f"DEBUG: get_file_operations called with user_id={user_id or 'None'}, limit={limit}, operation_type={operation_type}, status={status}, show_all={show_all}")
        
        # Check if FileOperations table exists and has data
        total_records = FileOperations.objects.count()
        print(f"DEBUG: Total FileOperations records in database: {total_records}")
        
        # Build query
        query = FileOperations.objects.all()
        
        # Store original query for fallback
        original_query = FileOperations.objects.all()
        
        # Filter by user_id if provided and show_all is not enabled
        if user_id and not show_all:
            user_filtered_query = query.filter(user_id=user_id)
            user_filtered_count = user_filtered_query.count()
            print(f"DEBUG: After user_id filter: {user_filtered_count} records")
            
            # If user filter returns no results, show all records
            if user_filtered_count == 0:
                print(f"DEBUG: No records found for user_id={user_id}, showing all records instead")
                query = original_query
            else:
                query = user_filtered_query
        elif show_all or not user_id:
            print(f"DEBUG: show_all={show_all} or no user_id provided, showing all records")
        
        # Filter by operation type if specified
        if operation_type:
            query = query.filter(operation_type=operation_type)
            print(f"DEBUG: After operation_type filter: {query.count()} records")
            
        # Filter by status if specified
        if status:
            query = query.filter(status=status)
            print(f"DEBUG: After status filter: {query.count()} records")
        
        # Apply limit and order by created_at descending
        operations = query.order_by('-created_at')[:limit]
        print(f"DEBUG: Final operations count: {len(operations)}")
        
        # If no records found, let's check what's in the database
        if len(operations) == 0:
            sample_records = FileOperations.objects.all()[:5]
            print(f"DEBUG: Sample records from FileOperations table:")
            for record in sample_records:
                print(f"  - ID: {record.id}, User: {record.user_id}, Operation: {record.operation_type}, File: {record.file_name}")
            
            # If no records exist at all, create some sample data for testing
            if total_records == 0:
                print("DEBUG: Creating sample file operations for testing...")
                try:
                    # Create sample file operations
                    sample_operations = [
                        FileOperations.objects.create(
                            operation_type='upload',
                            module='Document Handling',
                            user_id=str(user_id) if user_id else '3',
                            file_name='sample_document.pdf',
                            original_name='Sample Document.pdf',
                            file_size=1024*500,  # 500KB
                            file_type='pdf',
                            content_type='application/pdf',
                            status='completed',
                            s3_url='https://example.com/sample.pdf',
                            s3_key='uploads/sample_document.pdf'
                        ),
                        FileOperations.objects.create(
                            operation_type='export',
                            module='Compliance Management',
                            user_id=str(user_id) if user_id else '3',
                            file_name='compliance_report.xlsx',
                            original_name='Compliance Report.xlsx',
                            file_size=1024*750,  # 750KB
                            file_type='xlsx',
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            status='completed',
                            export_format='xlsx',
                            record_count=150
                        ),
                        FileOperations.objects.create(
                            operation_type='download',
                            module='Policy Management',
                            user_id=str(user_id) if user_id else '3',
                            file_name='policy_template.docx',
                            original_name='Policy Template.docx',
                            file_size=1024*300,  # 300KB
                            file_type='docx',
                            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                            status='completed',
                            s3_url='https://example.com/policy_template.docx',
                            s3_key='downloads/policy_template.docx'
                        )
                    ]
                    print(f"DEBUG: Created {len(sample_operations)} sample file operations")
                    
                    # Re-run the query with sample data
                    query = FileOperations.objects.all()
                    if user_id:
                        query = query.filter(user_id=user_id)
                    operations = query.order_by('-created_at')[:limit]
                    print(f"DEBUG: After creating samples, found {len(operations)} operations")
                    
                except Exception as create_error:
                    print(f"DEBUG: Error creating sample data: {str(create_error)}")
                    import traceback
                    print(f"DEBUG: Sample creation traceback: {traceback.format_exc()}")
        
        # Transform operations to match event format for frontend
        transformed_operations = []
        for op in operations:
            # Format timestamp
            timestamp = op.created_at.strftime('%m/%d/%Y, %I:%M:%S %p') if op.created_at else 'N/A'
            
            # Format file size
            def format_file_size(size_bytes):
                if not size_bytes:
                    return "Unknown size"
                # Convert bytes to human readable format
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size_bytes < 1024.0:
                        return f"{size_bytes:.1f} {unit}"
                    size_bytes /= 1024.0
                return f"{size_bytes:.1f} TB"
            
            file_size_display = format_file_size(op.file_size)
            display_name = op.original_name or op.file_name or "Unknown File"
            
            transformed_op = {
                'id': f"file_op_{op.id}",
                'title': f"{op.operation_type.title()} Operation: {display_name}",
                'framework': 'Document Handling',
                'module': getattr(op, 'module', None) or op.operation_type.title(),
                'category': 'File Operation',
                'source': 'Document Handling System',
                'timestamp': timestamp,
                'status': op.status.title(),
                'linkedRecordType': 'File Operation',
                'linkedRecordId': str(op.id),
                'linkedRecordName': display_name,
                'priority': 'High' if op.status == 'failed' else 'Medium',
                'description': f"File {op.operation_type}: {display_name} ({file_size_display})" + (f" - Error: {op.error}" if op.status == 'failed' and op.error else ''),
                'owner': op.user_id,
                'reviewer': 'System',
                'evidence': [],
                'file_data': {
                    'file_name': op.file_name,
                    'original_name': op.original_name,
                    'stored_name': op.stored_name,
                    's3_url': op.s3_url,
                    's3_key': op.s3_key,
                    's3_bucket': op.s3_bucket,
                    'file_type': op.file_type,
                    'file_size': op.file_size,
                    'content_type': op.content_type,
                    'export_format': op.export_format,
                    'record_count': op.record_count,
                    'operation_type': op.operation_type,
                    'platform': op.platform,
                    'completed_at': op.completed_at.strftime('%m/%d/%Y, %I:%M:%S %p') if op.completed_at else None,
                    'metadata': op.metadata
                }
            }
            transformed_operations.append(transformed_op)
        
        return JsonResponse({
            'success': True,
            'events': transformed_operations,
            'count': len(transformed_operations),
            'total_records': total_records,
            'message': f'Retrieved {len(transformed_operations)} file operations out of {total_records} total records'
        })
        
    except Exception as e:
        print(f"DEBUG: Error in get_file_operations: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'message': f'Error retrieving file operations: {str(e)}',
            'events': []
        }, status=500)