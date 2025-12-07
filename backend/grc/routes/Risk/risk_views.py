from ...routes.Global.s3_fucntions import export_data
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from django.http import JsonResponse, HttpResponse
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
import json
import logging
import tempfile
import os
from pathlib import Path
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator

# Set up logger
logger = logging.getLogger(__name__)

# RBAC imports
from ...rbac.decorators import rbac_required, require_any_permission, require_all_permissions
from ...rbac.permissions import (
    RiskViewPermission, RiskCreatePermission, RiskEditPermission, 
    RiskApprovePermission, RiskAssignPermission, RiskEvaluatePermission,
    RiskAnalyticsPermission, IncidentViewPermission, IncidentCreatePermission,
    IncidentEditPermission, ViewAllCompliancePermission,ComplianceViewPermission
)

# Framework filtering helper
from .framework_filter_helper import (
    apply_framework_filter, 
    apply_framework_filter_to_risk_instances,
    get_framework_sql_filter,
    get_framework_filter_info
)

# Import secure file upload utilities from incident views
from ..Incident.incident_views import (
    SecureFileUploadHandler, get_s3_client, get_client_ip, send_log
)
from ...routes.Consent import require_consent

# DRF Session auth variant that skips CSRF enforcement for API clients
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return



@csrf_exempt
@api_view(['POST', 'OPTIONS'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([RiskViewPermission])  # RBAC: Require RiskViewPermission for exporting risk register
def export_risk_register_v2(request):
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Max-Age'] = '86400'
        return response
    
    try:
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8')) if request.body else {}
        else:
            data = request.data if hasattr(request, 'data') else {}
            
        export_format = data.get('export_format', 'json')
        risk_data = data.get('risk_data', [])
        user_id = data.get('user_id', 'default_user')
        file_name = data.get('file_name', 'risk_register_export')
        
        # Log the request for debugging
        import datetime
        request_start = datetime.datetime.now()
        print(f"\n{'='*80}")
        print(f"📥 [ROUTE] Export request received at {request_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        print(f"   ├─ Format: {export_format}")
        print(f"   ├─ User ID: {user_id}")
        print(f"   ├─ File name: {file_name}")
        print(f"   ├─ Data size: {len(str(risk_data)):,} characters ({len(str(risk_data)) / (1024*1024):.2f} MB)")
        print(f"   └─ Records count: {len(risk_data) if isinstance(risk_data, list) else 1:,}")
        
        # Simple export logic without external service dependency
        if export_format == 'json':
            response = JsonResponse({
                'success': True,
                'data': risk_data,
                'format': 'json',
                'file_name': f"{file_name}.json"
            })
            # Add CORS headers
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        elif export_format == 'csv':
            import csv
            from io import StringIO
            
            output = StringIO()
            if risk_data and len(risk_data) > 0:
                writer = csv.DictWriter(output, fieldnames=risk_data[0].keys())
                writer.writeheader()
                writer.writerows(risk_data)
            
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{file_name}.csv"'
            # Add CORS headers
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        else:
            # Try to use export_data from s3_fucntions.py
            try:
                print(f"\n🔄 [ROUTE] Calling s3_fucntions.export_data() for format: {export_format}")
                route_call_start = datetime.datetime.now()
                
                result = export_data(
                    data=risk_data,
                    file_format=export_format,
                    user_id=user_id,
                    options={
                        'file_name': file_name
                    }
                )
                
                route_call_time = (datetime.datetime.now() - route_call_start).total_seconds()
                total_route_time = (datetime.datetime.now() - request_start).total_seconds()
                
                print(f"\n📤 [ROUTE] Export function completed in {route_call_time:.2f} seconds")
                print(f"   ├─ Success: {result.get('success', False)}")
                if result.get('success'):
                    print(f"   ├─ File URL: {result.get('file_url', 'N/A')}")
                    print(f"   ├─ File name: {result.get('file_name', 'N/A')}")
                else:
                    print(f"   ├─ Error: {result.get('error', 'Unknown error')}")
                print(f"   └─ Total route time: {total_route_time:.2f} seconds")
                
                print(f"\n{'='*80}")
                print(f"✅ [ROUTE] Response sent - Total time: {total_route_time:.2f} seconds")
                print(f"{'='*80}\n")
                
                response = JsonResponse(result)
                # Add CORS headers
                response['Access-Control-Allow-Origin'] = '*'
                response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
                response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                return response
            except Exception as export_error:
                route_call_time = (datetime.datetime.now() - route_call_start).total_seconds()
                total_route_time = (datetime.datetime.now() - request_start).total_seconds()
                print(f"\n❌ [ROUTE] Export service error after {route_call_time:.2f} seconds: {str(export_error)}")
                print(f"   └─ Total route time: {total_route_time:.2f} seconds")
                import traceback
                traceback.print_exc()
                print(f"\n{'='*80}")
                print(f"❌ [ROUTE] ERROR - Total time: {total_route_time:.2f} seconds")
                print(f"{'='*80}\n")
                return JsonResponse({
                    "success": False, 
                    "error": f"Export format '{export_format}' not supported. Error: {str(export_error)}"
                }, status=400)
                
    except Exception as e:
        print(f"❌ Export endpoint error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([ComplianceViewPermission])  # RBAC: Require RiskViewPermission for exporting compliance management
def export_compliance_management(request):
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.data
        export_format = data.get('export_format', 'json')
        compliance_data = data.get('compliance_data', [])
        user_id = data.get('user_id', 'default_user')
        file_name = data.get('file_name', 'compliance_management_export')
        
        # Simple export logic without external service dependency
        if export_format == 'json':
            return JsonResponse({
                'success': True,
                'data': compliance_data,
                'format': 'json',
                'file_name': f"{file_name}.json"
            })
        elif export_format == 'csv':
            import csv
            from io import StringIO
            
            output = StringIO()
            if compliance_data and len(compliance_data) > 0:
                writer = csv.DictWriter(output, fieldnames=compliance_data[0].keys())
                writer.writeheader()
                writer.writerows(compliance_data)
            
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{file_name}.csv"'
            return response
        else:
            # Try to use export_data from s3_fucntions.py
            try:
                result = export_data(
                    data=compliance_data,
                    file_format=export_format,
                    user_id=user_id,
                    options={
                        'file_name': file_name
                    }
                )
                return JsonResponse(result)
            except Exception as export_error:
                return JsonResponse({
                    "success": False, 
                    "error": f"Export format '{export_format}' not supported. Error: {str(export_error)}"
                }, status=400)
                
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)



from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from ...serializers import UserSerializer
from rest_framework import viewsets
from ...models import Risk
from ...serializers import RiskSerializer
from ...serializers import UserSerializer, RiskWorkflowSerializer
from rest_framework import viewsets
from ...models import Risk, RiskAssignment
from ...serializers import RiskSerializer, RiskInstanceSerializer
from ...models import Incident
from ...serializers import IncidentSerializer
from ...models import Compliance
from ...serializers import ComplianceSerializer
from ...models import RiskInstance
from ...serializers import RiskInstanceSerializer
from .slm_service import analyze_security_incident
from django.http import JsonResponse
from django.db.models import Count, Q, Avg, F, ExpressionWrapper, DurationField, FloatField, Sum
from .slm_service import analyze_security_incident
from django.contrib.auth.models import User
import datetime
import json
import random
import traceback
import uuid
from rest_framework import generics
from ...models import GRCLog
from ...serializers import GRCLogSerializer
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import connection
from dateutil.relativedelta import relativedelta
from django.db import models
from django.db.models.functions import Cast
import decimal
from decimal import Decimal
import requests
from ...models import CategoryBusinessUnit
from ...models import Users

# Helper function to convert Decimal objects to float for JSON serialization
def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    else:
        return obj


LOGGING_SERVICE_URL = None  # Disabled external logging service

def send_log(module, actionType, description=None, userId=None, userName=None,
             userRole=None, entityType=None, logLevel='INFO', ipAddress=None,
             additionalInfo=None, entityId=None):
    
    # Create log entry in database
    try:
        # Prepare data for GRCLog model
        log_data = {
            'Module': module,
            'ActionType': actionType,
            'Description': description,
            'UserId': userId,
            'UserName': userName,
            'EntityType': entityType,
            'EntityId': entityId,
            'LogLevel': logLevel,
            'IPAddress': ipAddress,
            'AdditionalInfo': additionalInfo
        }
        
        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        # Create and save the log entry
        log_entry = GRCLog(**log_data)
        log_entry.save()
        
        # Optionally still send to logging service if needed
        try:
            if LOGGING_SERVICE_URL:
                # Format for external service (matches expected format in loggingservice.js)
                api_log_data = {
                    "module": module,
                    "actionType": actionType,  # This is exactly what the service expects
                    "description": description,
                    "userId": userId,
                    "userName": userName,
                    "userRole": userRole,
                    "entityType": entityType,
                    "logLevel": logLevel,
                    "ipAddress": ipAddress,
                    "additionalInfo": additionalInfo
                }
                # Clean out None values
                api_log_data = {k: v for k, v in api_log_data.items() if v is not None}
                
                response = requests.post(LOGGING_SERVICE_URL, json=api_log_data)
                if response.status_code != 200:
                    print(f"Failed to send log to service: {response.text}")
        except Exception as e:
            print(f"Error sending log to service: {str(e)}")
            
        return log_entry.LogId  # Return the ID of the created log
    except Exception as e:
        print(f"Error saving log to database: {str(e)}")
        # Try to capture the error itself
        try:
            error_log = GRCLog(
                Module=module,
                ActionType='LOG_ERROR',
                Description=f"Error logging {actionType} on {module}: {str(e)}",
                LogLevel='ERROR'
            )
            error_log.save()
        except:
            pass  # If we can't even log the error, just continue
        return None


@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([RiskViewPermission])  # RBAC: Require RiskViewPermission for login
def login(request):
    from ...models import Users
    from django.contrib.auth.hashers import check_password
    
    send_log(
        module="Auth",
        actionType="LOGIN",
        description="User login attempt",
        userId=None,
        userName=request.data.get('username'),
        entityType="User"
    )
    
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'success': False,
            'message': 'Username and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Check if user exists in database
        user = Users.objects.filter(UserName=username).first()
        
        if user and user.Password == password:  # Note: You should use hashed passwords in production
            return Response({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user.UserId,
                    'username': user.UserName,
                    'email': user.email
                }
            })
        else:
            return Response({
                'success': False,
                'message': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Authentication error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([RiskCreatePermission])  # RBAC: Require RiskCreatePermission for user registration
def register(request):
    send_log(
        module="Auth",
        actionType="REGISTER",
        description="User registration attempt",
        userId=None,
        userName=request.data.get('username', ''),
        entityType="User"
    )
    
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'token': str(refresh.access_token),
            'refresh': str(refresh),
            'user': serializer.data
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@rbac_required(required_permission='view_all_risk')
def test_connection(request):
    send_log(
        module="System",
        actionType="TEST",
        description="API connection test",
        userId=request.user.id if request.user.is_authenticated else None,
        userName=request.user.username if request.user.is_authenticated else None
    )
    
    return Response({"message": "Connection successful!"})

@api_view(['GET'])
@rbac_required(required_permission='view_all_incident')
def last_incident(request):
    send_log(
        module="Incident",
        actionType="VIEW",
        description="Viewing last incident",
        userId=request.user.id if request.user.is_authenticated else None,
        userName=request.user.username if request.user.is_authenticated else None,
        entityType="Incident"
    )
    
    last = Incident.objects.order_by('-IncidentId').first()
    if last:
        serializer = IncidentSerializer(last)
        return Response(serializer.data)
    else:
        return Response({}, status=404)

@api_view(['GET'])
@rbac_required(required_permission='view_all_compliance')
def get_compliance_by_incident(request, incident_id):
    send_log(
        module="Compliance",
        actionType="VIEW",
        description=f"Viewing compliance for incident {incident_id}",
        userId=request.user.id if request.user.is_authenticated else None,
        userName=request.user.username if request.user.is_authenticated else None,
        entityType="Compliance",
        additionalInfo={"incident_id": incident_id}
    )
    
    try:
        # Find the incident
        incident = Incident.objects.get(IncidentId=incident_id)
        
        # Find related compliance(s) where ComplianceId matches the incident's ComplianceId
        if incident.ComplianceId:
            compliance = Compliance.objects.filter(ComplianceId=incident.ComplianceId).first()
            if compliance:
                serializer = ComplianceSerializer(compliance)
                return Response(serializer.data)
        
        return Response({"message": "No related compliance found"}, status=404)
    except Incident.DoesNotExist:
        return Response({"message": "Incident not found"}, status=404)

@api_view(['GET'])
@rbac_required(required_permission='view_all_risk')
def get_risks_by_incident(request, incident_id):
    send_log(
        module="Risk",
        actionType="VIEW",
        description=f"Viewing risks for incident {incident_id}",
        userId=request.user.id if request.user.is_authenticated else None,
        userName=request.user.username if request.user.is_authenticated else None,
        entityType="Risk",
        additionalInfo={"incident_id": incident_id}
    )
    
    try:
        # Find the incident
        incident = Incident.objects.get(IncidentId=incident_id)
        
        # Get compliance ID from the incident
        compliance_id = incident.ComplianceId
        
        if compliance_id:
            # Find all risks with the same compliance ID
            risks = Risk.objects.filter(ComplianceId=compliance_id)
            
            if risks.exists():
                serializer = RiskSerializer(risks, many=True)
                return Response(serializer.data)
        
        return Response({"message": "No related risks found"}, status=404)
    except Incident.DoesNotExist:
        return Response({"message": "Incident not found"}, status=404)

class RiskViewSet(viewsets.ModelViewSet):
    queryset = Risk.objects.all()
    serializer_class = RiskSerializer
    authentication_classes = [CsrfExemptSessionAuthentication, BasicAuthentication]
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'list' or self.action == 'retrieve':
            permission_classes = [RiskViewPermission]
        elif self.action == 'create':
            permission_classes = [RiskCreatePermission]
        elif self.action == 'update' or self.action == 'partial_update':
            permission_classes = [RiskEditPermission]
        elif self.action == 'destroy':
            permission_classes = [RiskEditPermission]
        else:
            permission_classes = [RiskViewPermission]
        
        return [permission() for permission in permission_classes]
    
    def list(self, request):
        send_log(
            module="Risk",
            actionType="LIST",
            description="Viewing all risks",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Risk"
        )
        
        try:
            # Get all risks with department and business unit information
            from django.db import connection
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        r.RiskId,
                        r.ComplianceId,
                        r.RiskTitle,
                        r.Criticality,
                        r.PossibleDamage,
                        r.Category,
                        r.RiskType,
                        r.BusinessImpact,
                        r.RiskDescription,
                        r.RiskLikelihood,
                        r.RiskImpact,
                        r.RiskExposureRating,
                        r.RiskPriority,
                        r.RiskMitigation,
                        r.CreatedAt,
                        u.UserName as CreatedBy,
                        CONCAT(u.FirstName, ' ', u.LastName) as CreatedByName,
                        d.DepartmentName,
                        bu.Name as BusinessUnitName
                    FROM risk r
                    LEFT JOIN risk_instance ri ON r.RiskId = ri.RiskId
                    LEFT JOIN users u ON ri.UserId = u.UserId
                    LEFT JOIN department d ON u.DepartmentId = d.DepartmentId
                    LEFT JOIN businessunits bu ON d.BusinessUnitId = bu.BusinessUnitId
                    ORDER BY r.CreatedAt DESC
                """)
                
                columns = [col[0] for col in cursor.description]
                risks_data = []
                
                for row in cursor.fetchall():
                    risk_dict = dict(zip(columns, row))
                    risks_data.append(risk_dict)
            
            return Response({
                'success': True,
                'risks': risks_data
            })
            
        except Exception as e:
            print(f"Error fetching risks with department info: {str(e)}")
            # Fallback to original method
        return super().list(request)
    
    def retrieve(self, request, pk=None):
        send_log(
            module="Risk",
            actionType="VIEW",
            description=f"Viewing risk {pk}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Risk",
            additionalInfo={"risk_id": pk}
        )
        return super().retrieve(request, pk)
    
    @csrf_exempt
    @require_consent('create_risk')
    def create(self, request):
        print(f"RiskViewSet.create called with data: {request.data}")
        print(f"Request user: {request.user}")
        print(f"Request authenticated: {request.user.is_authenticated}")
         # Add framework ID from session/context
        from .framework_filter_helper import get_active_framework_filter
        framework_id = get_active_framework_filter(request)
        # Make request data mutable
        if hasattr(request.data, '_mutable'):
            request.data._mutable = True
        
        if framework_id:
            # Add framework ID if one is selected
            request.data['FrameworkId'] = framework_id
            print(f"✅ [RISK CREATE] Adding FrameworkId to new risk: {framework_id}")
        else:
            # No framework selected - allow NULL/None
            request.data['FrameworkId'] = None
            print("ℹ️ [RISK CREATE] No framework selected - creating risk without framework ID")
        
        send_log(
            module="Risk",
            actionType="CREATE",
            description="Creating new risk",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Risk"
        )
        
        try:
            result = super().create(request)
            print(f"Risk created successfully: {result.data}")
            return result
        except Exception as e:
            print(f"Error creating risk: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def update(self, request, pk=None):
        send_log(
            module="Risk",
            actionType="UPDATE",
            description=f"Updating risk {pk}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Risk",
            additionalInfo={"risk_id": pk}
        )
        return super().update(request, pk)
    
    def destroy(self, request, pk=None):
        send_log(
            module="Risk",
            actionType="DELETE",
            description=f"Deleting risk {pk}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Risk",
            additionalInfo={"risk_id": pk}
        )
        return super().destroy(request, pk)

class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'list' or self.action == 'retrieve':
            permission_classes = [IncidentViewPermission]
        elif self.action == 'create':
            permission_classes = [IncidentCreatePermission]
        elif self.action == 'update' or self.action == 'partial_update':
            permission_classes = [IncidentEditPermission]
        elif self.action == 'destroy':
            permission_classes = [IncidentEditPermission]
        else:
            permission_classes = [IncidentViewPermission]
        
        return [permission() for permission in permission_classes]
    
    def list(self, request):
        send_log(
            module="Incident",
            actionType="LIST",
            description="Viewing all incidents",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident"
        )
        return super().list(request)
    
    def retrieve(self, request, pk=None):
        send_log(
            module="Incident",
            actionType="VIEW",
            description=f"Viewing incident {pk}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident",
            additionalInfo={"incident_id": pk}
        )
        return super().retrieve(request, pk)
    
    def create(self, request):
        send_log(
            module="Incident",
            actionType="CREATE",
            description="Creating new incident",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident"
        )
        return super().create(request)
    
    def update(self, request, pk=None):
        send_log(
            module="Incident",
            actionType="UPDATE",
            description=f"Updating incident {pk}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident",
            additionalInfo={"incident_id": pk}
        )
        return super().update(request, pk)
    
    def destroy(self, request, pk=None):
        send_log(
            module="Incident",
            actionType="DELETE",
            description=f"Deleting incident {pk}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident",
            additionalInfo={"incident_id": pk}
        )
        return super().destroy(request, pk)

class ComplianceViewSet(viewsets.ModelViewSet):
    queryset = Compliance.objects.all()
    serializer_class = ComplianceSerializer
    lookup_field = 'ComplianceId'
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'list' or self.action == 'retrieve':
            permission_classes = [ViewAllCompliancePermission]
        elif self.action == 'create':
            permission_classes = [ViewAllCompliancePermission]  # Using view permission as there's no separate create permission
        elif self.action == 'update' or self.action == 'partial_update':
            permission_classes = [ViewAllCompliancePermission]
        elif self.action == 'destroy':
            permission_classes = [ViewAllCompliancePermission]
        else:
            permission_classes = [ViewAllCompliancePermission]
        
        return [permission() for permission in permission_classes]
    
    def list(self, request):
        send_log(
            module="Compliance",
            actionType="LIST",
            description="Viewing all compliances",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Compliance"
        )
        return super().list(request)
    
    def retrieve(self, request, ComplianceId=None):
        send_log(
            module="Compliance",
            actionType="VIEW",
            description=f"Viewing compliance {ComplianceId}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Compliance",
            additionalInfo={"compliance_id": ComplianceId}
        )
        return super().retrieve(request, ComplianceId=ComplianceId)
    
    def create(self, request):
        send_log(
            module="Compliance",
            actionType="CREATE",
            description="Creating new compliance",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Compliance"
        )
        return super().create(request)
    
    def update(self, request, ComplianceId=None):
        send_log(
            module="Compliance",
            actionType="UPDATE",
            description=f"Updating compliance {ComplianceId}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Compliance",
            additionalInfo={"compliance_id": ComplianceId}
        )
        return super().update(request, ComplianceId=ComplianceId)
    
    def destroy(self, request, ComplianceId=None):
        send_log(
            module="Compliance",
            actionType="DELETE",
            description=f"Deleting compliance {ComplianceId}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Compliance",
            additionalInfo={"compliance_id": ComplianceId}
        )
        return super().destroy(request, ComplianceId=ComplianceId)

class RiskInstanceViewSet(viewsets.ModelViewSet):
    queryset = RiskInstance.objects.all()
    serializer_class = RiskInstanceSerializer
    authentication_classes = [CsrfExemptSessionAuthentication, BasicAuthentication]
   
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'list' or self.action == 'retrieve':
            permission_classes = [RiskViewPermission]
        elif self.action == 'create':
            permission_classes = [RiskCreatePermission]
        elif self.action == 'update' or self.action == 'partial_update':
            permission_classes = [RiskEditPermission]
        elif self.action == 'destroy':
            permission_classes = [RiskEditPermission]
        else:
            permission_classes = [RiskViewPermission]
       
        return [permission() for permission in permission_classes]
   
    def list(self, request, *args, **kwargs):
        """Override to use raw SQL and avoid date conversion issues"""
        try:
            # Use the risk_instances_view function which handles dates correctly
            # Pass the original Django HttpRequest object instead of the DRF Request
            return risk_instances_view(request._request)
        except Exception as e:
            print(f"Error in RiskInstanceViewSet.list: {e}")
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)
   
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single risk instance by ID"""
        try:
            # Get the risk instance ID from the URL
            instance_id = kwargs.get('pk')
           
            # Log the view operation
            send_log(
                module="Risk",
                actionType="VIEW",
                description=f"Viewing risk instance {instance_id}",
                userId=request.user.id if request.user.is_authenticated else None,
                userName=request.user.username if request.user.is_authenticated else None,
                entityType="RiskInstance",
                additionalInfo={"risk_id": instance_id}
            )
           
            # Use raw SQL query to avoid ORM date conversion issues
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM risk_instance WHERE RiskInstanceId = %s
                """, [instance_id])
               
                columns = [col[0] for col in cursor.description]
                row = cursor.fetchone()
               
                if not row:
                    return Response({"error": f"Risk instance with id {instance_id} not found"}, status=404)
               
                # Convert row to dictionary
                instance_dict = dict(zip(columns, row))
               
                # Convert date objects to string to avoid utcoffset error
                if 'MitigationDueDate' in instance_dict and instance_dict['MitigationDueDate']:
                    instance_dict['MitigationDueDate'] = instance_dict['MitigationDueDate'].isoformat()
               
                if 'Date' in instance_dict and instance_dict['Date']:
                    instance_dict['Date'] = instance_dict['Date'].isoformat()
               
                if 'MitigationCompletedDate' in instance_dict and instance_dict['MitigationCompletedDate']:
                    instance_dict['MitigationCompletedDate'] = instance_dict['MitigationCompletedDate'].isoformat()
           
            return Response(instance_dict)
        except Exception as e:
            print(f"Error retrieving risk instance: {e}")
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)
   
    def create(self, request, *args, **kwargs):
        # Log the create operation
        send_log(
            module="Risk",
            actionType="CREATE",
            description="Creating new risk instance",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="RiskInstance"
        )
       
        print("Original request data:", request.data)
       
        try:
            # Create a mutable copy of the data
            mutable_data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
           
            # Remove Date field if present as it's been replaced with CreatedAt
            if 'Date' in mutable_data:
                del mutable_data['Date']
           
            # Set default values for fields that might cause issues
            if not mutable_data.get('RiskOwner'):
                mutable_data['RiskOwner'] = "System Owner"
           
            # Only set RiskStatus if not provided, and use a valid default
            if not mutable_data.get('RiskStatus'):
                mutable_data['RiskStatus'] = "Not Assigned"
               
            # Handle JSON fields properly
            for field in ['RiskMitigation', 'ModifiedMitigations', 'RiskFormDetails']:
                if field in mutable_data:
                    if not mutable_data[field] or mutable_data[field] == '':
                        if field == 'RiskMitigation':
                            mutable_data[field] = {}
                        else:
                            mutable_data[field] = None
           
            # Handle date fields
            for date_field in ['MitigationDueDate', 'MitigationCompletedDate']:
                if date_field in mutable_data and mutable_data[date_field] == '':
                    mutable_data[date_field] = None
                   
            # Get risk_id for RecurrenceCount calculation
            risk_id = mutable_data.get('RiskId')
           
            if risk_id is not None:
                # Count existing instances with the same RiskId
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) FROM risk_instance WHERE RiskId = %s
                    """, [risk_id])
                    existing_count = cursor.fetchone()[0]
                    # Set recurrence count to existing count + 1
                    mutable_data['RecurrenceCount'] = existing_count + 1
            else:
                mutable_data['RecurrenceCount'] = 1  # fallback
           
            print("Processed data:", mutable_data)
           
            # Create a serializer with our processed data
            serializer = self.get_serializer(data=mutable_data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=201, headers=headers)
       
        except Exception as e:
            print(f"Error creating risk instance: {e}")
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)
 
    @csrf_exempt
    def update(self, request, *args, **kwargs):
        # Log the update operation
        instance = self.get_object()
        send_log(
            module="Risk",
            actionType="UPDATE",
            description=f"Updating risk instance {instance.RiskInstanceId}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="RiskInstance",
            additionalInfo={"risk_id": instance.RiskInstanceId}
        )
 
        # Accept partial updates to avoid 400s when frontend sends only changed fields
        try:
            # Make a mutable copy to normalize a few common fields
            mutable_data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
 
            # Normalize empty JSON/date fields so serializer doesn't fail
            for field in ['RiskMitigation', 'ModifiedMitigations', 'RiskFormDetails']:
                if field in mutable_data and (mutable_data[field] == '' or mutable_data[field] is None):
                    mutable_data[field] = {} if field == 'RiskMitigation' else None
 
            for date_field in ['MitigationDueDate', 'MitigationCompletedDate']:
                if date_field in mutable_data and mutable_data[date_field] == '':
                    mutable_data[date_field] = None
 
            serializer = self.get_serializer(instance, data=mutable_data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except Exception as e:
            print(f"Error updating risk instance {instance.RiskInstanceId}: {e}")
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=400)
   
    def destroy(self, request, *args, **kwargs):
        # Log the delete operation
        instance = self.get_object()
        send_log(
            module="Risk",
            actionType="DELETE",
            description=f"Deleting risk instance {instance.RiskInstanceId}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="RiskInstance",
            additionalInfo={"risk_id": instance.RiskInstanceId}
        )
       
        return super().destroy(request, *args, **kwargs)
 

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@rbac_required(required_permission='create_risk')
def analyze_incident(request):
    send_log(
        module="Incident",
        actionType="ANALYZE",
        description="Analyzing incident with SLM model",
        userId=request.user.id if request.user.is_authenticated else None,
        userName=request.user.username if request.user.is_authenticated else None,
        entityType="Incident",
        additionalInfo={"title": request.data.get('title', '')}
    )
    
    try:
        incident_description = request.data.get('description', '')
        incident_title = request.data.get('title', '')
        
        # Validate input data
        if not incident_title and not incident_description:
            return Response({
                "error": "Both title and description cannot be empty. Please provide at least one field for analysis."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Combine title and description for better context
        full_incident = f"Title: {incident_title}\n\nDescription: {incident_description}"
        
        print(f"Analyzing incident - Title: {incident_title}")
        print(f"Analyzing incident - Description: {incident_description}")
        
        # Call the SLM function
        analysis_result = analyze_security_incident(full_incident)
        
        print(f"Analysis result: {analysis_result}")
        
        # Validate the analysis result
        if not analysis_result or not isinstance(analysis_result, dict):
            return Response({
                "error": "Failed to generate valid analysis. Please try again or use manual mode."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Ensure all required fields are present
        required_fields = ['criticality', 'possibleDamage', 'category', 'riskDescription', 
                          'riskLikelihood', 'riskLikelihoodJustification', 'riskImpact', 'riskImpactJustification', 
                          'riskExposureRating', 'riskPriority', 'riskMitigation']
        
        for field in required_fields:
            if field not in analysis_result:
                analysis_result[field] = ""
        
        # Ensure riskMitigation is an array
        if not isinstance(analysis_result.get('riskMitigation'), list):
            analysis_result['riskMitigation'] = []
        
        return Response(analysis_result)
        
    except Exception as e:
        print(f"Error in analyze_incident: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return Response({
            "error": f"An error occurred during analysis: {str(e)}. Please try again or use manual mode."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@rbac_required(required_permission='risk_performance_analytics')
def risk_metrics(request):
    """
    Get risk metrics with optional time filter
    """
    time_range = request.GET.get('timeRange', 'all')
    category = request.GET.get('category', 'all')
    priority = request.GET.get('priority', 'all')
    
    print(f"FILTER REQUEST: timeRange={time_range}, category={category}, priority={priority}")
    
    # Start with all risk instances
    queryset = RiskInstance.objects.all()
    print(f"Initial queryset count: {queryset.count()}")
    
    # Print columns and raw data for debugging
    print("Available columns:", [f.name for f in RiskInstance._meta.fields])
    
    # Sample data dump for debugging (first 5 records)
    print("Sample data:")
    for instance in queryset[:5]:
        print(f"ID: {instance.RiskInstanceId}, Category: {instance.Category}, Priority: {instance.RiskPriority}, Status: {instance.RiskStatus}")
    
    # Apply time filter if not 'all'
    if time_range != 'all':
        today = timezone.now().date()
        if time_range == '7days':
            start_date = today - timedelta(days=7)
        elif time_range == '30days':
            start_date = today - timedelta(days=30)
        elif time_range == '90days':
            start_date = today - timedelta(days=90)
        elif time_range == '1year':
            start_date = today - timedelta(days=365)
        else:
            start_date = None
            
        if start_date:
            queryset = queryset.filter(CreatedAt__gte=start_date)
            print(f"After time filter ({time_range}): {queryset.count()} records")
    
    # Apply category filter if not 'all'
    if category != 'all':
        # Handle the case conversion between frontend and backend naming
        category_map = {
            'operational': 'Operational',
            'financial': 'Financial',
            'strategic': 'Strategic', 
            'compliance': 'Compliance',
            'it-security': 'IT Security'
        }
        db_category = category_map.get(category, category)
        queryset = queryset.filter(Category__iexact=db_category)
        print(f"After category filter ({db_category}): {queryset.count()} records")
    
    # Apply priority filter if not 'all'
    if priority != 'all':
        # Handle the case conversion between frontend and backend naming
        priority_map = {
            'critical': 'Critical',
            'high': 'High',
            'medium': 'Medium',
            'low': 'Low'
        }
        db_priority = priority_map.get(priority, priority)
        queryset = queryset.filter(RiskPriority__iexact=db_priority)
        print(f"After priority filter ({db_priority}): {queryset.count()} records")
    
    # Calculate metrics
    total_risks = queryset.count()
    print(f"Final filtered count: {total_risks} records")
    
    # Accepted risks: Count risks with RiskStatus "Assigned" or "Approved"
    accepted_risks = queryset.filter(
        Q(RiskStatus__iexact='Assigned') | Q(RiskStatus__iexact='Approved')
    ).count()
    print(f"Accepted risks (Assigned or Approved): {accepted_risks}")
    
    # Rejected risks: Count risks with RiskStatus "Rejected"
    rejected_risks = queryset.filter(RiskStatus__iexact='Rejected').count()
    print(f"Rejected risks: {rejected_risks}")

    # Mitigated risks: Count rows with "Completed" in MitigationStatus
    mitigated_risks = 0
    in_progress_risks = 0
    
    # Print all distinct RiskStatus values to help debugging
    statuses = queryset.values_list('RiskStatus', flat=True).distinct()
    print(f"All RiskStatus values in filtered data: {list(statuses)}")
    
    try:
        # First try directly with ORM if MitigationStatus field exists
        if 'MitigationStatus' in [f.name for f in RiskInstance._meta.fields]:
            print("Trying ORM for MitigationStatus counts")
            mitigated_risks = queryset.filter(MitigationStatus=RiskInstance.MITIGATION_COMPLETED).count()
            in_progress_risks = queryset.filter(MitigationStatus=RiskInstance.MITIGATION_IN_PROGRESS).count()
            print(f"ORM counts - Mitigated: {mitigated_risks}, In Progress: {in_progress_risks}")
        
        # If that doesn't work or returns 0, try with direct SQL
        if mitigated_risks == 0 and in_progress_risks == 0:
            print("Trying direct SQL for MitigationStatus counts")
            with connection.cursor() as cursor:
                # First create a list of all the IDs from the queryset to use in our SQL
                risk_ids = list(queryset.values_list('RiskInstanceId', flat=True))
                
                if risk_ids:
                    # Convert the list to a comma-separated string for SQL
                    risk_ids_str = ','.join(map(str, risk_ids))
                    
                    # Check if MitigationStatus column exists
                    cursor.execute("SHOW COLUMNS FROM risk_instance LIKE 'MitigationStatus'")
                    mitigation_status_exists = cursor.fetchone() is not None
                    print(f"MitigationStatus column exists: {mitigation_status_exists}")
                    
                    if mitigation_status_exists:
                        # Count mitigated risks
                        sql = f"SELECT COUNT(*) FROM risk_instance WHERE RiskInstanceId IN ({risk_ids_str}) AND MitigationStatus = 'Completed'"
                        print(f"Executing SQL: {sql}")
                        cursor.execute(sql)
                        row = cursor.fetchone()
                        mitigated_risks = row[0] if row else 0
                        
                        # Count in-progress risks
                        sql = f"SELECT COUNT(*) FROM risk_instance WHERE RiskInstanceId IN ({risk_ids_str}) AND MitigationStatus = 'Work in Progress'"
                        print(f"Executing SQL: {sql}")
                        cursor.execute(sql)
                        row = cursor.fetchone()
                        in_progress_risks = row[0] if row else 0
                        
                        print(f"SQL counts - Mitigated: {mitigated_risks}, In Progress: {in_progress_risks}")
    except Exception as e:
        print(f"Error getting mitigated/in-progress risks: {e}")
    
    response_data = {
        'total': total_risks,
        'accepted': accepted_risks,
        'rejected': rejected_risks,
        'mitigated': mitigated_risks,
        'inProgress': in_progress_risks
    }
    print(f"Final response: {response_data}")
    
    return Response(response_data)





@api_view(['GET'])
@rbac_required(required_permission='risk_performance_analytics')
# OLD FUNCTION REMOVED - Using updated version below that handles all filters (framework_id, policy_id, etc.)
# def risk_metrics_by_category - see line 4561 for the active version

def generate_dates(days=30):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return [start_date + timedelta(days=i) for i in range(days)]




@api_view(['GET'])
@permission_classes([RiskViewPermission])  # RBAC: Require RiskViewPermission for viewing users
def get_users(request):
    send_log(
        module="User",
        actionType="VIEW",
        description="Viewing all users",
        userId=request.user.id if request.user.is_authenticated else None,
        userName=request.user.username if request.user.is_authenticated else None,
        entityType="User"
    )
    
    users = Users.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@rbac_required(required_permission='view_all_risk')
def risk_workflow(request):
    """Get all risk instances for the workflow view"""
    try:
        # Fetch all risk instances with framework filtering
        risk_instances = apply_framework_filter_to_risk_instances(RiskInstance.objects.all(), request)
        
        # Log the view action
        send_log(
            module="Risk",
            actionType="VIEW",
            description="User viewed risk workflow",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="RiskInstance"
        )
        
        # If there are no instances, print a debug message
        if not risk_instances.exists():
            print("No risk instances found in the database")
            
        data = []
        
        for risk in risk_instances:
            # Create response data
            risk_data = {
                'RiskInstanceId': risk.RiskInstanceId,
                'RiskId': risk.RiskId,
                'RiskDescription': risk.RiskDescription,
                'Criticality': risk.Criticality,
                'Category': risk.Category,
                'RiskStatus': risk.RiskStatus,
                'RiskPriority': risk.RiskPriority,
                'RiskImpact': risk.RiskImpact,
                'MitigationDueDate': risk.MitigationDueDate,
                'MitigationStatus': risk.MitigationStatus,
                'ReviewerCount': risk.ReviewerCount or 0,
                'assignedTo': None
            }
            
            # Try to find an assignment if possible
            try:
                if risk.RiskId:
                    risk_obj = Risk.objects.filter(RiskId=risk.RiskId).first()
                    if risk_obj:
                        assignment = RiskAssignment.objects.filter(risk=risk_obj).first()
                        if assignment:
                            risk_data['assignedTo'] = assignment.assigned_to.username
            except Exception as e:
                print(f"Error checking assignment: {e}")
                
            data.append(risk_data)
        
                # Print debug info
        filter_info = get_framework_filter_info(request)
        print(f"Returning {len(data)} risk instances (filtered: {filter_info['is_filtered']})")
        
        # Add framework filter info to the response
        response_data = {
            'risks': data,
            'filter_info': filter_info
        }
        return Response(response_data)
        
    except Exception as e:
        # Log the error
        send_log(
            module="Risk",
            actionType="VIEW",
            description=f"Error viewing risk workflow: {str(e)}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="RiskInstance",
            logLevel="ERROR"
        )
        print(f"Error in risk_workflow view: {e}")
        return Response({"error": str(e)}, status=500)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@rbac_required(required_permission='assign_risk')
def assign_risk_instance(request):
    """Assign a risk instance to a user from custom user table"""
    risk_id = request.data.get('risk_id')
    # Try to get user_id from either field name (UserId or user_id)
    user_id = request.data.get('UserId') or request.data.get('user_id')
    mitigations = request.data.get('mitigations')
    due_date = request.data.get('due_date')
    risk_form_details = request.data.get('risk_form_details')
    
    # Log the assignment request
    send_log(
        module="Risk",
        actionType="ASSIGN",
        description=f"Assigning risk {risk_id} to user {user_id}",
        userId=request.user.id if request.user.is_authenticated else None,
        userName=request.user.username if request.user.is_authenticated else None,
        entityType="RiskInstance",
        additionalInfo={"risk_id": risk_id, "assigned_to": user_id}
    )
    
    if not risk_id or not user_id:
        return Response({'error': 'Risk ID and User ID are required'}, status=400)
    
    try:
        # Get the risk instance
        risk_instance = RiskInstance.objects.get(RiskInstanceId=risk_id)
        
        # For custom users we don't use Django ORM
        # Just validate the user exists
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT UserId, UserName FROM grc.users WHERE UserId = %s", [user_id])
            user = cursor.fetchone()
        
        if not user:
            return Response({'error': 'User not found'}, status=404)
        
        # Update risk instance with assigned user
        risk_instance.RiskOwner = user[1]  # UserName
        risk_instance.UserId = user_id
        risk_instance.RiskStatus = 'Assigned'  # Update to assigned status when admin assigns
        
        # Set form details if provided
        if risk_form_details:
            risk_instance.RiskFormDetails = risk_form_details
        
        # Set mitigation due date if provided
        if due_date:
            from datetime import datetime
            try:
                # Just use the date string directly, don't convert to datetime
                risk_instance.MitigationDueDate = due_date
            except ValueError:
                print(f"Invalid date format: {due_date}")
        
        # Save mitigations if provided
        if mitigations:
            print(f"Saving mitigations to RiskMitigation field: {mitigations}")
            # Store in RiskMitigation first
            risk_instance.RiskMitigation = mitigations
            # Also copy to ModifiedMitigations
            risk_instance.ModifiedMitigations = mitigations
        
        # Set default MitigationStatus
        risk_instance.MitigationStatus = RiskInstance.MITIGATION_YET_TO_START
        
        risk_instance.save()
        print(f"Risk instance updated successfully with mitigations: {risk_instance.RiskMitigation}")
        
        # Log success or failure
        if risk_instance:
            send_log(
                module="Risk",
                actionType="ASSIGN",
                description=f"Successfully assigned risk {risk_id} to user {user_id}",
                userId=request.user.id if request.user.is_authenticated else None,
                userName=request.user.username if request.user.is_authenticated else None,
                entityType="RiskInstance",
                additionalInfo={"risk_id": risk_id, "assigned_to": user_id}
            )
            return Response({'success': True})
        else:
            send_log(
                module="Risk",
                actionType="ASSIGN",
                description=f"Failed to assign risk {risk_id}: {str(e)}",
                userId=request.user.id if request.user.is_authenticated else None,
                userName=request.user.username if request.user.is_authenticated else None,
                entityType="RiskInstance",
                logLevel="ERROR",
                additionalInfo={"risk_id": risk_id, "assigned_to": user_id}
            )
            return Response({'error': str(e)}, status=500)
    except RiskInstance.DoesNotExist:
        return Response({'error': 'Risk instance not found'}, status=404)
    except Exception as e:
        print(f"Error assigning risk: {e}")
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@rbac_required(required_permission='view_all_risk')
def get_custom_users(request):
    """Get users from the custom user table"""
    send_log(
        module="User",
        actionType="VIEW",
        description="Viewing custom users",
        userId=request.user.id if request.user.is_authenticated else None,
        userName=request.user.username if request.user.is_authenticated else None,
        entityType="CustomUser"
    )
    
    try:
        # Using raw SQL query to fetch from your custom table
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM grc.users")
            columns = [col[0] for col in cursor.description]
            users = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
            
            # Map the field names for compatibility
            for user in users:
                # Add user_id field for compatibility with frontend
                if 'UserId' in user and 'user_id' not in user:
                    user['user_id'] = user['UserId']
                # Add UserName field for compatibility with frontend
                if 'UserName' in user and 'user_name' not in user:
                    user['user_name'] = user['UserName']
                    
        return Response(users)
    except Exception as e:
        print(f"Error fetching custom users: {e}")
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@rbac_required(required_permission='view_all_risk')
def get_custom_user(request, user_id):
    """Get a single user from the custom user table by ID"""
    send_log(
        module="User",
        actionType="VIEW",
        description=f"Viewing custom user {user_id}",
        userId=request.user.id if request.user.is_authenticated else None,
        userName=request.user.username if request.user.is_authenticated else None,
        entityType="CustomUser",
        entityId=user_id
    )
    
    try:
        # Using raw SQL query to fetch from your custom table
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM grc.users WHERE UserId = %s", [user_id])
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            
            if not row:
                return Response({"error": f"User with ID {user_id} not found"}, status=404)
                
            user = dict(zip(columns, row))
            
            # Map the field names for compatibility
            if 'UserId' in user and 'user_id' not in user:
                user['user_id'] = user['UserId']
            if 'UserName' in user and 'user_name' not in user:
                user['user_name'] = user['UserName']
                    
        return Response(user)
    except Exception as e:
        print(f"Error fetching custom user {user_id}: {e}")
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@rbac_required(required_permission='view_all_risk')
def risk_instances_view(request):
    """Simple view to return all risk instances with proper date handling"""
    try:
        import random
        from django.db import connection
        from rest_framework.request import Request
        
        # Convert to DRF Request if needed
        if not isinstance(request, Request):
            from rest_framework.request import Request
            request = Request(request)
        
        # Get framework filter
        framework_where, framework_params = get_framework_sql_filter(request)
        
        # Get available departments and business units
        available_departments = []
        available_business_units = []
        
        with connection.cursor() as cursor:
            # Fetch all departments
            cursor.execute("SELECT DepartmentName FROM department WHERE DepartmentName IS NOT NULL AND DepartmentName != ''")
            available_departments = [row[0] for row in cursor.fetchall()]
            
            # Fetch all business units
            cursor.execute("SELECT Name FROM businessunits WHERE Name IS NOT NULL AND Name != ''")
            available_business_units = [row[0] for row in cursor.fetchall()]
        
        # Fallback lists if database is empty
        if not available_departments:
            available_departments = ['Core Banking IT', 'Customer Service', 'Information Security', 'Risk Management']
        
        if not available_business_units:
            available_business_units = ['Compliance Division (CD001)', 'IT Operations Unit (IT002)', 'Retail Banking (RB003)']
        
         # Use raw SQL query to avoid ORM date conversion issues and include department/business unit info
        # Apply framework filter through Risk relation
        with connection.cursor() as cursor:
            # Build query with framework filter
            framework_join_where = ""
            if framework_where:
                # Replace "r.FrameworkId" with "risk.FrameworkId" for this query
                framework_join_where = framework_where.replace("r.FrameworkId", "risk.FrameworkId")
            
            query = f"""
                SELECT 
                    ri.*,
                    u.UserName as CreatedBy,
                    CONCAT(u.FirstName, ' ', u.LastName) as CreatedByName,
                    d.DepartmentName,
                    bu.Name as BusinessUnitName,
                    risk.FrameworkId
                FROM risk_instance ri
                LEFT JOIN risk ON ri.RiskId = risk.RiskId
                LEFT JOIN users u ON ri.UserId = u.UserId
                LEFT JOIN department d ON u.DepartmentId = d.DepartmentId
                LEFT JOIN businessunits bu ON d.BusinessUnitId = bu.BusinessUnitId
                WHERE 1=1 {framework_join_where}
                ORDER BY ri.CreatedAt DESC
            """
            cursor.execute(query, framework_params)
            columns = [col[0] for col in cursor.description]
            risk_instances_data = []
            
            for row in cursor.fetchall():
                # Convert row to dictionary
                instance_dict = dict(zip(columns, row))
                
                # Convert date objects to string to avoid utcoffset error
                if 'MitigationDueDate' in instance_dict and instance_dict['MitigationDueDate']:
                    instance_dict['MitigationDueDate'] = instance_dict['MitigationDueDate'].isoformat()
                
                if 'Date' in instance_dict and instance_dict['Date']:
                    instance_dict['Date'] = instance_dict['Date'].isoformat()
                
                if 'MitigationCompletedDate' in instance_dict and instance_dict['MitigationCompletedDate']:
                    instance_dict['MitigationCompletedDate'] = instance_dict['MitigationCompletedDate'].isoformat()
                
                # Assign random department if missing or N/A
                if not instance_dict.get('DepartmentName') or instance_dict.get('DepartmentName') == 'N/A' or instance_dict.get('DepartmentName') is None:
                    instance_dict['DepartmentName'] = random.choice(available_departments)
                
                # Assign random business unit if missing or N/A
                if not instance_dict.get('BusinessUnitName') or instance_dict.get('BusinessUnitName') == 'N/A' or instance_dict.get('BusinessUnitName') is None:
                    instance_dict['BusinessUnitName'] = random.choice(available_business_units)
                
                # Ensure CreatedBy fields have defaults
                instance_dict['CreatedBy'] = instance_dict.get('CreatedBy') or 'System'
                instance_dict['CreatedByName'] = instance_dict.get('CreatedByName') or 'System User'
                
                risk_instances_data.append(instance_dict)
        
        return Response(risk_instances_data)
    except Exception as e:
        print(f"Error fetching risk instances: {e}")
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@rbac_required(required_permission='view_all_risk')
def get_user_risks(request, user_id):
    """Get all risks assigned to a specific user, including completed ones"""
    try:
        # Log the view action
        send_log(
            module="Risk",
            actionType="VIEW",
            description=f"Viewing risks assigned to user {user_id}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="RiskInstance",
            additionalInfo={"viewed_user_id": user_id}
        )
        
        # For debugging - check if the user exists in the custom user table
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT user_id FROM grc.users WHERE user_id = %s", [user_id])
                user = cursor.fetchone()
                
            if not user:
                print(f"User with ID {user_id} not found in grc.users table, but continuing anyway")
                # Return empty list instead of 404
                return Response([])
        except Exception as db_error:
            print(f"Error checking user existence: {db_error}")
            # Continue even if there's an error checking the user

        # Get framework filter
        framework_where, framework_params = get_framework_sql_filter(request)
        
        # Add user_id to params
        params = {'user_id': user_id}
        params.update(framework_params)
        
        # Query risks that have the specific user assigned with department and business unit info
        from django.db import connection
        with connection.cursor() as cursor:
            query = f"""
                SELECT 
                    ri.*,
                    u.UserName as CreatedBy,
                    CONCAT(u.FirstName, ' ', u.LastName) as CreatedByName,
                    d.DepartmentName,
                    bu.Name as BusinessUnitName
                FROM risk_instance ri
                LEFT JOIN users u ON ri.UserId = u.UserId
                LEFT JOIN department d ON u.DepartmentId = d.DepartmentId
                LEFT JOIN businessunits bu ON d.BusinessUnitId = bu.BusinessUnitId
                LEFT JOIN risk r ON ri.RiskId = r.RiskId
                WHERE ri.UserId = %(user_id)s
                {framework_where.replace('r.FrameworkId', 'r.FrameworkId')}
                ORDER BY ri.CreatedAt DESC
            """
            cursor.execute(query, params)
            
            columns = [col[0] for col in cursor.description]
            data = []
            
            for row in cursor.fetchall():
                risk_data = dict(zip(columns, row))
                
                # Convert date objects to string to avoid utcoffset error
                if 'MitigationDueDate' in risk_data and risk_data['MitigationDueDate']:
                    risk_data['MitigationDueDate'] = risk_data['MitigationDueDate'].isoformat()
                
                if 'CreatedAt' in risk_data and risk_data['CreatedAt']:
                    risk_data['CreatedAt'] = risk_data['CreatedAt'].isoformat()
                
                data.append(risk_data)
        
        if not data:
            print(f"No risk instances found for user {user_id}")
            return Response([])  # Return empty list instead of error
        
        # Sort by status - active tasks first, then completed tasks
        sorted_data = sorted(data, key=lambda x: (
            0 if x['RiskStatus'] == 'Work In Progress' else
            1 if x['RiskStatus'] == 'Under Review' else
            2 if x['RiskStatus'] == 'Revision Required' else
            3 if x['RiskStatus'] == 'Approved' else 4
        ))
        
        # Get framework filter info
        filter_info = get_framework_filter_info(request)
        print(f"Returning {len(sorted_data)} risk instances for user {user_id} (filtered: {filter_info['is_filtered']})")
        
        # Add framework filter info to the response
        response_data = {
            'risks': sorted_data,
            'filter_info': filter_info
        }
        return Response(response_data)
    
    except Exception as e:
        send_log(
            module="Risk",
            actionType="VIEW",
            description=f"Error viewing user risks: {str(e)}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="RiskInstance",
            logLevel="ERROR",
            additionalInfo={"viewed_user_id": user_id}
        )
        print(f"Error fetching user risks: {e}")
        # Return empty list instead of error
        return Response([])

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@rbac_required(required_permission='edit_risk')
def update_risk_status(request):
    """Update the status of a risk instance"""
    risk_id = request.data.get('risk_id')
    status = request.data.get('status')
    
    # Log the status update request
    send_log(
        module="Risk",
        actionType="UPDATE",
        description=f"Updating risk {risk_id} status to {status}",
        userId=request.user.id if request.user.is_authenticated else None,
        userName=request.user.username if request.user.is_authenticated else None,
        entityType="RiskInstance",
        additionalInfo={"risk_id": risk_id, "new_status": status}
    )
    
    if not risk_id or not status:
        return Response({'error': 'Risk ID and status are required'}, status=400)
    
    try:
        # Get the risk instance
        risk_instance = RiskInstance.objects.get(RiskInstanceId=risk_id)
        
        # Update the status
        risk_instance.RiskStatus = status
        risk_instance.save()
        
        return Response({
            'success': True,
            'message': f'Risk status updated to {status}'
        })
    except RiskInstance.DoesNotExist:
        return Response({'error': 'Risk instance not found'}, status=404)
    except Exception as e:
        print(f"Error updating risk status: {e}")
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@rbac_required(required_permission='view_all_risk')
def get_risk_mitigations(request, risk_id):
    """Get mitigation steps for a specific risk"""
    send_log(
        module="Risk",
        actionType="VIEW",
        description=f"Viewing mitigations for risk {risk_id}",
        userId=request.user.id if request.user.is_authenticated else None,
        userName=request.user.username if request.user.is_authenticated else None,
        entityType="RiskMitigation",
        additionalInfo={"risk_id": risk_id}
    )
    
    try:
        # Get the risk instance
        risk_instance = RiskInstance.objects.get(RiskInstanceId=risk_id)
        
        # Check if there are mitigations in the RiskMitigation field
        if not risk_instance.RiskMitigation:
            # If no specific mitigation steps, create a generic one
            mitigations = [{
                "title": "Step 1",
                "description": "No detailed mitigation workflow available.",
                "status": "Not Started"
            }]
        else:
            # Try to parse the RiskMitigation field as JSON
            try:
                # Handle string format (most common case)
                if isinstance(risk_instance.RiskMitigation, str):
                    # Parse the JSON string
                    parsed_data = json.loads(risk_instance.RiskMitigation)
                    
                    # Handle numbered object format: {"1": "Step 1", "2": "Step 2", ...}
                    if isinstance(parsed_data, dict) and all(k.isdigit() or (isinstance(k, int)) for k in parsed_data.keys()):
                        mitigations = []
                        # Sort keys numerically
                        ordered_keys = sorted(parsed_data.keys(), key=lambda k: int(k) if isinstance(k, str) else k)
                        
                        for key in ordered_keys:
                            mitigations.append({
                                "title": f"Step {key}",
                                "description": parsed_data[key],
                                "status": "Not Started"
                            })
                    # Handle array format
                    elif isinstance(parsed_data, list):
                        mitigations = parsed_data
                    # Handle other object formats
                    else:
                        mitigations = [parsed_data]
                        
                # Handle direct object format (already parsed)
                elif isinstance(risk_instance.RiskMitigation, dict):
                    parsed_data = risk_instance.RiskMitigation
                    # Handle numbered object
                    if all(k.isdigit() or (isinstance(k, int)) for k in parsed_data.keys()):
                        mitigations = []
                        ordered_keys = sorted(parsed_data.keys(), key=lambda k: int(k) if isinstance(k, str) else k)
                        
                        for key in ordered_keys:
                            mitigations.append({
                                "title": f"Step {key}",
                                "description": parsed_data[key],
                                "status": "Not Started"
                            })
                    else:
                        mitigations = [parsed_data]
                        
                # Handle direct array format
                elif isinstance(risk_instance.RiskMitigation, list):
                    mitigations = risk_instance.RiskMitigation
                    
                # Handle unexpected format
                else:
                    mitigations = [{
                        "title": "Step 1",
                        "description": str(risk_instance.RiskMitigation),
                        "status": "Not Started"
                    }]
                    
            except json.JSONDecodeError:
                # If it's not valid JSON, create a single step with the text
                mitigations = [{
                    "title": "Step 1",
                    "description": risk_instance.RiskMitigation,
                    "status": "Not Started"
                }]
            except Exception as e:
                print(f"Error parsing mitigations: {e}")
                mitigations = [{
                    "title": "Step 1",
                    "description": f"Error parsing mitigation data: {str(e)}",
                    "status": "Error"
                }]
        
        # Add default fields if they're missing
        for i, step in enumerate(mitigations):
            if "title" not in step:
                step["title"] = f"Step {i+1}"
            if "description" not in step:
                step["description"] = "No description provided"
            if "status" not in step:
                step["status"] = "Not Started"
            # Set locked state based on previous steps
            step["locked"] = i > 0  # All steps except first are initially locked
        
        return Response(mitigations)
    
    except RiskInstance.DoesNotExist:
        return Response([{
            "title": "Error",
            "description": "Risk instance not found",
            "status": "Error"
        }], status=404)
    except Exception as e:
        print(f"Error fetching risk mitigations: {e}")
        return Response([{
            "title": "Error",
            "description": f"Server error: {str(e)}",
            "status": "Error"
        }], status=500)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@rbac_required(required_permission='approve_risk')
def update_mitigation_approval(request):
    """Update the approval status of a mitigation step"""
    approval_id = request.data.get('approval_id')
    mitigation_id = request.data.get('mitigation_id')
    approved = request.data.get('approved')
    remarks = request.data.get('remarks', '')
    
    send_log(
        module="Risk",
        actionType="APPROVE_MITIGATION",
        description=f"Updating mitigation approval for risk {approval_id}, mitigation {mitigation_id}, approved: {approved}",
        userId=request.user.id if request.user.is_authenticated else None,
        userName=request.user.username if request.user.is_authenticated else None,
        entityType="RiskMitigation",
        additionalInfo={"approval_id": approval_id, "mitigation_id": mitigation_id, "approved": approved}
    )
    
    if not approval_id or not mitigation_id:
        return Response({'error': 'Approval ID and mitigation ID are required'}, status=400)
    
    try:
        # Get the latest approval record by RiskInstanceId
        from django.db import connection
        with connection.cursor() as cursor:
            # Get the latest version for this risk
            cursor.execute("""
                SELECT ra.ExtractedInfo, ra.UserId, ra.ApproverId, ra.version 
                FROM grc.risk_approval ra
                WHERE ra.RiskInstanceId = %s
                ORDER BY 
                    CASE 
                        WHEN ra.version LIKE 'U%_update%' THEN 1
                        WHEN ra.version LIKE 'U%' THEN 2
                        WHEN ra.version LIKE 'R%_update%' THEN 3
                        WHEN ra.version LIKE 'R%' THEN 4
                        ELSE 5
                    END,
                    ra.version DESC
                LIMIT 1
            """, [approval_id])
            row = cursor.fetchone()
            
            if not row:
                return Response({'error': 'Approval record not found'}, status=404)
            
            import json
            extracted_info, user_id, approver_id, current_version = row[0], row[1], row[2], row[3]
            extracted_info_dict = json.loads(extracted_info)
            
            # Create a working copy to modify
            if 'mitigations' in extracted_info_dict and mitigation_id in extracted_info_dict['mitigations']:
                extracted_info_dict['mitigations'][mitigation_id]['approved'] = approved
                extracted_info_dict['mitigations'][mitigation_id]['remarks'] = remarks
                
                # Create an interim update version
                # If version already has _update suffix, don't add it again
                update_version = current_version + "_update" if "_update" not in current_version else current_version
                
                # Insert a new record with the interim version
                cursor.execute("""
                    INSERT INTO grc.risk_approval 
                    (RiskInstanceId, version, ExtractedInfo, UserId, ApproverId)
                    VALUES (%s, %s, %s, %s, %s)
                """, [
                    approval_id,
                    update_version,
                    json.dumps(extracted_info_dict),
                    user_id,
                    approver_id
                ])
                
                return Response({
                    'success': True,
                    'message': f'Mitigation {mitigation_id} approval status updated'
                })
            else:
                return Response({'error': 'Mitigation ID not found in approval record'}, status=404)
    except Exception as e:
        print(f"Error updating mitigation approval: {e}")
        return Response({'error': str(e)}, status=500)


def get_reviewer_id(reviewer_name):
    """Get the reviewer ID for a given reviewer name"""
    try:

        print(type(reviewer_name),'--------------saddaes-----------------------------')
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT user_id FROM grc.users WHERE user_name = %s", [reviewer_name])
            row = cursor.fetchone()
            print(row,'-------------------------------------------')
            if row:
                return row[0]
            else:
                return None
    except Exception as e:
        print(f"Error getting reviewer ID: {e}")
        return None

        
@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@rbac_required(required_permission='assign_risk')
def assign_reviewer(request):
    """Assign a reviewer to a risk instance and create approval record"""

    print(request.data,'-------------------------------------------')
    risk_id = request.data.get('risk_id')
    # Try to get reviewer_id from either field name (ReviewerId or reviewer_id)
    reviewer_id = request.data.get('ReviewerId') or request.data.get('reviewer_id')
    
    # Normalize empty strings to None
    if reviewer_id == '' or reviewer_id is None:
        reviewer_id = None

    print(f"Received reviewer_id: {reviewer_id}, Type: {type(reviewer_id)}")
    # Try to get user_id from either field name (UserId or user_id)
    user_id = request.data.get('UserId') or request.data.get('user_id')
    
    # Normalize empty strings to None
    if user_id == '' or user_id is None:
        user_id = None
    if risk_id == '' or risk_id is None:
        risk_id = None
    
    mitigations = request.data.get('mitigations')  # Get mitigation data with status
    risk_form_details = request.data.get('risk_form_details', None)  # Get form details
    create_approval_record = request.data.get('create_approval_record', False)  # Flag to determine if we should create approval record
    
    # Validate required fields before proceeding
    if not risk_id:
        return Response({'error': 'Risk ID is required'}, status=400)
    
    if not reviewer_id:
        return Response({'error': 'Reviewer ID is required. Please select a reviewer before submitting.'}, status=400)
    
    if not user_id:
        return Response({'error': 'User ID is required'}, status=400)
    
    # Ensure user_id is a string for the logging service
    user_id_str = str(user_id) if user_id is not None else None
    
    # Log the reviewer assignment
    send_log(
        module="Risk",
        actionType="ASSIGN_REVIEWER",
        description=f"Assigning reviewer {reviewer_id} to risk {risk_id}",
        userId=user_id_str,  # Convert to string to avoid the error
        entityType="RiskApproval",
        additionalInfo={"risk_id": risk_id, "reviewer_id": reviewer_id}
    )
    
    try:
        # Get the risk instance
        risk_instance = RiskInstance.objects.get(RiskInstanceId=risk_id)
        
        # Update form details if provided
        if risk_form_details:
            risk_instance.RiskFormDetails = risk_form_details
        
        # Check if reviewer_id is a string name or numeric ID
        from django.db import connection
        reviewer = None
        
        if isinstance(reviewer_id, str) and not reviewer_id.isdigit():
            # It's a name, look up the ID
            with connection.cursor() as cursor:
                cursor.execute("SELECT UserId, UserName, email FROM grc.users WHERE UserName = %s", [reviewer_id])
                reviewer = cursor.fetchone()
                
                if not reviewer:
                    # Try to find by partial match
                    cursor.execute("SELECT UserId, UserName, email FROM grc.users WHERE UserName LIKE %s LIMIT 1", [f"%{reviewer_id}%"])
                    reviewer = cursor.fetchone()
        else:
            # It's already an ID or a string that can be converted to an ID
            with connection.cursor() as cursor:
                cursor.execute("SELECT UserId, UserName, email FROM grc.users WHERE UserId = %s", [reviewer_id])
                reviewer = cursor.fetchone()
        
        # Also get user info
        with connection.cursor() as cursor:
            cursor.execute("SELECT UserId, UserName, email FROM grc.users WHERE UserId = %s", [user_id])
            user = cursor.fetchone()
        
        if not reviewer:
            return Response({'error': f'Reviewer not found with identifier: {reviewer_id}'}, status=404)
        
        # Update the risk instance with reviewer information
        reviewer_id_value = int(reviewer[0]) if reviewer[0] else None  # Use the actual UserId from the database
        print(f"Setting ReviewerId to {reviewer_id_value} (type: {type(reviewer_id_value)})")
        risk_instance.ReviewerId = reviewer_id_value
        risk_instance.ReviewerName = reviewer[1]  # UserName
        # Set the Reviewer column with reviewer name
        risk_instance.Reviewer = reviewer[1]  # Store reviewer name in the Reviewer column
        
        # Only set these statuses if creating an approval record (from workflow submission)
        # For initial assignment from RiskResolution.vue, keep default status
        if create_approval_record:
            risk_instance.RiskStatus = 'Revision Required by Reviewer'  # Change from 'Assigned' to 'Revision Required by Reviewer'
            risk_instance.MitigationStatus = RiskInstance.MITIGATION_IN_PROGRESS  # User submitted, needs reviewer
        else:
            # For initial assignment, set status to 'Yet to Start'
            risk_instance.RiskStatus = 'Assigned'
            risk_instance.MitigationStatus = RiskInstance.MITIGATION_YET_TO_START
        
        # Initialize ReviewerCount if it's None
        if risk_instance.ReviewerCount is None:
            risk_instance.ReviewerCount = 0
            
        # Increment reviewer count when assigning a reviewer
        risk_instance.ReviewerCount += 1
        
        risk_instance.save()
        
        # Ensure ReviewerId is set correctly in the database with direct SQL update
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE grc.risk_instance
                SET ReviewerId = %s
                WHERE RiskInstanceId = %s
            """, [reviewer_id, risk_id])
        
        # Only create approval record if explicitly requested (from workflow submission)
        if create_approval_record:
            # Determine the next version number (U1, U2, etc.)
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT version FROM grc.risk_approval 
                    WHERE RiskInstanceId = %s AND version LIKE 'U%%'
                    ORDER BY CAST(SUBSTRING(version, 2) AS UNSIGNED) DESC
                    LIMIT 1
                """, [risk_id])
                row = cursor.fetchone()
                
                if not row or not row[0]:
                    version = "U1"  # First user submission
                else:
                    current_version = row[0]
                    # Extract number part and increment
                    if current_version.startswith('U'):
                        try:
                            number = int(current_version[1:])
                            version = f"U{number + 1}"
                        except ValueError:
                            version = "U1"
                    else:
                        version = "U1"  # Fallback to U1
            
            # Create a simplified JSON structure for ExtractedInfo
            import json
            from datetime import datetime  # Import datetime here to avoid the error
            
            # Use the mitigation data provided, or get from the risk instance
            mitigation_steps = {}
            if mitigations:
                # Use the provided mitigations data but don't set 'approved' field for initial submission
                is_first_submission = version == "U1"
                
                for key, value in mitigations.items():
                    # Handle case where value is a string
                    if isinstance(value, str):
                        mitigation_steps[key] = {
                            "description": value,
                            "status": "Completed",
                            "comments": "",
                            "user_submitted_date": datetime.now().isoformat()
                        }
                    else:
                        # Handle new file evidence format similar to incidents
                        mitigation_steps[key] = {
                            "description": value.get("description", ""),
                            "status": value.get("status", "Completed"),
                            "comments": value.get("comments", ""),
                            "user_submitted_date": datetime.now().isoformat()
                        }
                        
                        # Handle file evidence - support both legacy and new format
                        if "files" in value and isinstance(value["files"], list):
                            # New format with files array
                            mitigation_steps[key]["files"] = value["files"]
                            # Keep legacy fields for backward compatibility
                            if value["files"] and len(value["files"]) > 0:
                                first_file = value["files"][0]
                                mitigation_steps[key]["aws-file_link"] = first_file.get("aws-file_link", "")
                                mitigation_steps[key]["fileName"] = first_file.get("fileName", "")
                        else:
                            # Legacy format
                            mitigation_steps[key]["fileData"] = value.get("fileData", None)
                            mitigation_steps[key]["fileName"] = value.get("fileName", None)
                            mitigation_steps[key]["aws-file_link"] = value.get("aws-file_link", None)
                        
                        # Only set approved field if this is not the first submission or the value is coming from a previous approval
                        if not is_first_submission and "approved" in value:
                            if isinstance(value["approved"], bool):
                                mitigation_steps[key]["approved"] = value["approved"]
                                mitigation_steps[key]["remarks"] = value.get("remarks", "")
            
            # Create the simplified JSON structure
            extracted_info = {
                "risk_id": risk_id,
                "mitigations": mitigation_steps,
                "version": version,
                "submission_date": datetime.now().isoformat(),
                "user_submitted_date": datetime.now().isoformat(),  # Fixed: using datetime.now()
                "risk_form_details": risk_form_details  # Add form details to ExtractedInfo
            }
            
            # If risk_form_details has user_submitted_date, make sure it's in the top level as well
            if risk_form_details and 'user_submitted_date' in risk_form_details:
                extracted_info["user_submitted_date"] = risk_form_details["user_submitted_date"]
            
            # Insert into risk_approval table with ApprovedRejected as NULL for new submissions
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO grc.risk_approval 
                    (RiskInstanceId, version, ExtractedInfo, UserId, ApproverId, ApprovedRejected)
                    VALUES (%s, %s, %s, %s, %s, NULL)
                    """,
                    [
                        risk_id,
                        version,  # Use the version we calculated
                        json.dumps(extracted_info),
                        user_id,
                        reviewer_id
                    ]
                )
            
            # Send notification to reviewer about new mitigation to review
            try:
                notification_service = NotificationService()
                
                # Calculate review due date (5 days from now)
                from datetime import timedelta  # Import timedelta here
                review_due_date = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
                
                notification_data = {
                    'notification_type': 'riskMitigationCompleted',
                    'email': reviewer[2],  # reviewer email
                    'email_type': 'gmail',
                    'template_data': [
                        reviewer[1],  # reviewer name
                        risk_instance.RiskDescription or f"Risk #{risk_id}",  # risk title
                        user[1],  # mitigator name
                        review_due_date  # review due date
                    ]
                }
                
                notification_result = notification_service.send_multi_channel_notification(notification_data)
                print(f"Notification result: {notification_result}")
            except Exception as e:
                print(f"Error sending notification: {e}")
        
        return Response({
            'success': True,
            'message': f'Reviewer {reviewer[1]} assigned to risk' + (' and approval record created with version {version}' if create_approval_record else '')
        })
    except Exception as e:
        print(f"Error assigning reviewer: {e}")
        # Add traceback for more detailed error information
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@rbac_required(required_permission='evaluate_assigned_risk')
def get_reviewer_tasks(request, user_id):
    """Get all risks where the user is assigned as a reviewer, including completed ones"""
    send_log(
        module="Risk",
        actionType="VIEW",
        description=f"Viewing reviewer tasks for user {user_id}",
        userId=request.user.id if request.user.is_authenticated else None,
        userName=request.user.username if request.user.is_authenticated else None,
        entityType="RiskReview",
        additionalInfo={"reviewer_id": user_id}
    )
    
    try:
        # For debugging - check if the user exists in the custom user table
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT user_id FROM grc.users WHERE user_id = %s", [user_id])
                user = cursor.fetchone()
                
            if not user:
                print(f"User with ID {user_id} not found in grc.users table, but continuing anyway")
                # Return empty list instead of 404
                return Response([])
        except Exception as db_error:
            print(f"Error checking user existence: {db_error}")
            # Continue even if there's an error checking the user

                # Get framework filter
        framework_where, framework_params = get_framework_sql_filter(request)
        
        # Add user_id to params
        params = {'approver_id': user_id}
        params.update(framework_params)
            
            
        # Using raw SQL query to fetch from approval table
        from django.db import connection
        with connection.cursor() as cursor:
            # Try a simpler query first to see if there's any data
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM grc.risk_approval 
                    WHERE ApproverId = %s
                """, [user_id])
                count = cursor.fetchone()[0]
                
                if count == 0:
                    print(f"No reviewer tasks found for user {user_id}")
                    return Response([])
            except Exception as e:
                print(f"Error in count query: {e}")
                # Continue even if count query fails
                
            # Modified query to get only the latest version for each risk - simplified for compatibility
            # Now with framework filtering
            try:
                query = f"""
                    WITH latest_versions AS (
                        SELECT ra.RiskInstanceId, MAX(ra.version) as latest_version
                        FROM grc.risk_approval ra
                        WHERE ra.ApproverId = %(approver_id)s
                        GROUP BY ra.RiskInstanceId
                    )
                    SELECT ra.RiskInstanceId, ra.ExtractedInfo, ra.UserId, ra.ApproverId, ra.version,
                           ri.RiskDescription, ri.Criticality, ri.Category, ri.RiskStatus, ri.RiskPriority,
                           r.FrameworkId
                    FROM grc.risk_approval ra
                    JOIN latest_versions lv ON ra.RiskInstanceId = lv.RiskInstanceId AND ra.version = lv.latest_version
                    LEFT JOIN grc.risk_instance ri ON ra.RiskInstanceId = ri.RiskInstanceId
                    LEFT JOIN grc.risk r ON ri.RiskId = r.RiskId
                    WHERE ra.ApproverId = %(approver_id)s
                    {framework_where}
                """
                cursor.execute(query, params)
                columns = [col[0] for col in cursor.description]
                reviewer_tasks = []
                
                # Process each row to handle NULL values manually
                for row in cursor.fetchall():
                    row_dict = dict(zip(columns, row))
                    # Replace None values with defaults
                    for key in ['RiskDescription', 'Criticality', 'Category', 'RiskStatus', 'RiskPriority']:
                        if key in row_dict and row_dict[key] is None:
                            row_dict[key] = 'Unknown'
                    reviewer_tasks.append(row_dict)
            except Exception as e:
                print(f"Error in main reviewer query: {e}")
                return Response([])  # Return empty list on error
        
        # After fetching reviewer_tasks
        for task in reviewer_tasks:
            risk_id = task['RiskInstanceId']
            current_version = task['version']
            # Only for user versions (U2, U3, ...)
            if current_version.startswith('U'):
                try:
                    current_num = int(current_version[1:])
                    previous_num = current_num - 1
                    if previous_num > 0:
                        previous_version = f"U{previous_num}"
                        cursor.execute("""
                            SELECT ExtractedInfo
                            FROM grc.risk_approval
                            WHERE RiskInstanceId = %s AND version = %s
                            LIMIT 1
                        """, [risk_id, previous_version])
                        prev_row = cursor.fetchone()
                        if prev_row:
                            import json
                            try:
                                previous_data = json.loads(prev_row[0])
                                task['PreviousVersion'] = previous_data
                            except Exception:
                                task['PreviousVersion'] = None
                        else:
                            task['PreviousVersion'] = None
                    else:
                        task['PreviousVersion'] = None
                except Exception:
                    task['PreviousVersion'] = None
            else:
                task['PreviousVersion'] = None
        
        # Get framework filter info
        filter_info = get_framework_filter_info(request)
        print(f"Returning {len(reviewer_tasks)} reviewer tasks for user {user_id} (filtered: {filter_info['is_filtered']})")
        
        # Add framework filter info to the response
        response_data = {
            'tasks': reviewer_tasks,
            'filter_info': filter_info
        }
        return Response(response_data)
    except Exception as e:
        print(f"Error fetching reviewer tasks: {e}")
        # Return empty list instead of error for frontend compatibility
        return Response([])

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@rbac_required(required_permission='evaluate_assigned_risk')
def complete_review(request):
    """Complete the review process for a risk"""
    import json
    import datetime
    import traceback
    
    try:
        # Print request data for debugging
        print("Complete review request data:", request.data)
        
        approval_id = request.data.get('approval_id')  # This is RiskInstanceId
        risk_id = request.data.get('risk_id')
        approved = request.data.get('approved')
        mitigations = request.data.get('mitigations', {})  # Get all mitigations
        risk_form_details = request.data.get('risk_form_details', {})  # Get form details, default to empty dict
        
        # Make sure we have the necessary data
        if not risk_id:
            print("Missing risk_id in request data")
            return Response({'error': 'Risk ID is required'}, status=400)
            
        # Set approval_id to risk_id if it's missing
        if not approval_id:
            approval_id = risk_id
        
        try:
            # Get the risk instance to update statuses
            risk_instance = RiskInstance.objects.get(RiskInstanceId=risk_id)
        except RiskInstance.DoesNotExist:
            print(f"Risk instance with ID {risk_id} not found")
            return Response({'error': 'Risk instance not found'}, status=404)
        
        # Update risk form details if approved
        if approved and risk_form_details:
            # Convert empty strings to None/null in risk_form_details
            cleaned_form_details = {}
            for key, value in risk_form_details.items():
                # Skip empty or null values instead of storing them
                if value not in ['', None]:
                    cleaned_form_details[key] = value
            # Only update if we have any non-empty values
            if cleaned_form_details:
                risk_instance.RiskFormDetails = cleaned_form_details
        
        # Update risk status based on approval
        if approved:
            risk_instance.RiskStatus = 'Approved'
            risk_instance.MitigationStatus = RiskInstance.MITIGATION_COMPLETED
            # Set completion date when approved
            risk_instance.MitigationCompletedDate = datetime.datetime.now()
            # No need to increment reviewer count as this is the final approval
        else:
            risk_instance.RiskStatus = 'Revision Required by User'  # Change from 'Assigned' to 'Revision Required by User'
            risk_instance.MitigationStatus = RiskInstance.MITIGATION_REVISION_USER  # Reviewer submitted, needs user revision
            
            # Increment reviewer count only if not yet approved
            if risk_instance.ReviewerCount is None:
                risk_instance.ReviewerCount = 1
            else:
                risk_instance.ReviewerCount += 1
        
        try:
            risk_instance.save()
        except Exception as e:
            print(f"Error saving risk instance: {e}")
            traceback.print_exc()
            return Response({'error': 'Failed to save risk instance'}, status=500)
        
        # Get current approval record to get relevant data
        from django.db import connection
        with connection.cursor() as cursor:
            try:
                # Get the latest version
                cursor.execute("""
                    SELECT ExtractedInfo, UserId, ApproverId, version
                    FROM grc.risk_approval
                    WHERE RiskInstanceId = %s
                    ORDER BY version DESC
                    LIMIT 1
                """, [risk_id])
                
                row = cursor.fetchone()
                if not row:
                    return Response({'error': 'Approval record not found'}, status=404)
                    
                extracted_info, user_id, approver_id, current_version = row[0], row[1], row[2], row[3]
                
                # Determine the next R version
                cursor.execute("""
                    SELECT version FROM grc.risk_approval 
                    WHERE RiskInstanceId = %s AND version LIKE 'R%%'
                    ORDER BY version DESC
                    LIMIT 1
                """, [risk_id])
                
                row = cursor.fetchone()
                
                if not row or not row[0]:
                    # First reviewer version
                    new_version = "R1"
                else:
                    # Get the next reviewer version
                    current_r_version = row[0]
                    try:
                        # Extract the number part
                        number = int(current_r_version[1:])
                        new_version = f"R{number + 1}"
                    except ValueError:
                        new_version = "R1"
                
                # Create the new data structure directly matching your desired format
                try:
                    extracted_info_dict = json.loads(extracted_info)
                except json.JSONDecodeError:
                    print("Error decoding extracted_info JSON, using empty dict")
                    extracted_info_dict = {}
                
                # Build the new JSON structure with the exact format you want
                new_json = {
                    "risk_id": int(risk_id) if isinstance(risk_id, str) and risk_id.isdigit() else risk_id,
                    "version": new_version,
                    "mitigations": {},
                    "review_date": datetime.datetime.now().isoformat(),
                    "overall_approved": approved,
                    "risk_form_details": risk_form_details or extracted_info_dict.get("risk_form_details", {})  # Include form details
                }
                
                # Copy the mitigations from the request
                for mitigation_id, mitigation_data in mitigations.items():
                    # Include file data and comments in the stored JSON
                    mitigation_entry = {
                        "description": mitigation_data.get("description", ""),
                        "approved": mitigation_data.get("approved", False),
                        "remarks": mitigation_data.get("remarks", "") if not mitigation_data.get("approved", False) else "",
                        "comments": mitigation_data.get("comments", "")
                    }
                    
                    # Handle file evidence - support both legacy and new format
                    if "files" in mitigation_data and isinstance(mitigation_data["files"], list):
                        # New format with files array
                        mitigation_entry["files"] = mitigation_data["files"]
                        # Keep legacy fields for backward compatibility
                        if mitigation_data["files"] and len(mitigation_data["files"]) > 0:
                            first_file = mitigation_data["files"][0]
                            mitigation_entry["aws-file_link"] = first_file.get("aws-file_link", "")
                            mitigation_entry["fileName"] = first_file.get("fileName", "")
                    else:
                        # Legacy format
                        mitigation_entry["fileData"] = mitigation_data.get("fileData", None)
                        mitigation_entry["fileName"] = mitigation_data.get("fileName", None)
                        mitigation_entry["aws-file_link"] = mitigation_data.get("aws-file_link", None)
                    
                    new_json["mitigations"][mitigation_id] = mitigation_entry

                # Get framework ID for this risk instance
                from .framework_filter_helper import get_active_framework_filter
                framework_id = get_active_framework_filter(request)
                
                # Insert new record with the R version and set ApprovedRejected column
                cursor.execute("""
                    INSERT INTO grc.risk_approval 
                    (RiskInstanceId, version, ExtractedInfo, UserId, ApproverId, ApprovedRejected, FrameworkId)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [
                    risk_id,
                    new_version,
                    json.dumps(new_json),
                    user_id,
                    approver_id,
                    "Approved" if approved else "Rejected",
                    framework_id  # Add framework ID (can be None)
                ])
                if framework_id:
                    print(f"✅ [RISK REVIEW] Created review record with FrameworkId: {framework_id}")
                else:
                    print(f"ℹ️ [RISK REVIEW] Created review record without FrameworkId (None)")
                
                # Update the risk status based on approval
                risk_status = 'Approved' if approved else 'Revision Required by User'
                cursor.execute("""
                    UPDATE grc.risk_instance
                    SET RiskStatus = %s
                    WHERE RiskInstanceId = %s
                """, [risk_status, risk_id])
                
            except Exception as e:
                print(f"Database error: {e}")
                traceback.print_exc()
                return Response({'error': 'Database operation failed'}, status=500)

        send_log(
            module="Risk",
            actionType="COMPLETE_REVIEW",
            description=f"Completing review for risk {risk_id} with status: {'Approved' if approved else 'Rejected'}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="RiskApproval",
            additionalInfo={"risk_id": risk_id, "approved": approved}
        )
            
        return Response({
            'success': True,
            'message': f'Review completed and risk status updated to {risk_status} with version {new_version}'
        })
    except Exception as e:
        print(f"Error completing review: {e}")
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@rbac_required(required_permission='view_all_risk')
def get_user_notifications(request, user_id):
    """Get notifications for the user about their reviewed tasks"""
    try:
        send_log(
            module="Risk",
            actionType="VIEW",
            description=f"Viewing notifications for user {user_id}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Notification",
            additionalInfo={"user_id": user_id}
        )
        
        import json
        from django.db import connection
        
        # Check if risk_approval table exists
        with connection.cursor() as cursor:
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = DATABASE() AND table_name = 'risk_approval'
                """)
                table_exists = cursor.fetchone()[0] > 0
                
                if not table_exists:
                    print("risk_approval table doesn't exist, returning empty notifications")
                    return Response([])
            except Exception as e:
                print(f"Error checking table existence: {e}")
                return Response([])
        
        # Get notifications from risk_approval table
        with connection.cursor() as cursor:
            try:
                # Simplified query that doesn't assume specific schema name
                cursor.execute("""
                    SELECT 
                        ra.RiskInstanceId, 
                        ra.version,
                        ra.ExtractedInfo,
                        ra.ApprovedRejected,
                        ri.RiskDescription
                    FROM 
                        risk_approval ra
                    LEFT JOIN 
                        risk_instance ri ON ra.RiskInstanceId = ri.RiskInstanceId
                    WHERE 
                        ra.UserId = %s 
                        AND ra.version LIKE 'R%%'
                """, [user_id])
                
                columns = [col[0] for col in cursor.description]
                notifications = []
                
                for row in cursor.fetchall():
                    data = dict(zip(columns, row))
                    
                    # Extract approval info from JSON if available
                    try:
                        if data['ExtractedInfo'] and isinstance(data['ExtractedInfo'], str):
                            extracted_info = json.loads(data['ExtractedInfo'])
                            # Add relevant fields from extracted info
                            data['overall_approved'] = extracted_info.get('overall_approved')
                            data['review_date'] = extracted_info.get('review_date')
                            data['risk_id'] = extracted_info.get('risk_id')
                            
                            # Include any mitigation data if available
                            if 'mitigations' in extracted_info:
                                data['mitigations'] = extracted_info['mitigations']
                    except Exception as e:
                        print(f"Error parsing ExtractedInfo JSON: {e}")
                    
                    notifications.append(data)
                
                print(f"Found {len(notifications)} notifications for user {user_id}")
                return Response(notifications)
            except Exception as e:
                print(f"Error fetching notifications: {e}")
                import traceback
                traceback.print_exc()
                return Response([])
    except Exception as e:
        print(f"Error in notifications endpoint: {e}")
        import traceback
        traceback.print_exc()
        # Return empty array with 200 status
        return Response([])

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@rbac_required(required_permission='edit_risk')
def update_mitigation_status(request):
    """Update the mitigation status of a risk instance"""
    risk_id = request.data.get('risk_id')
    status = request.data.get('status')
    
    send_log(
        module="Risk",
        actionType="UPDATE",
        description=f"Updating mitigation status for risk {risk_id} to {status}",
        userId=request.user.id if request.user.is_authenticated else None,
        userName=request.user.username if request.user.is_authenticated else None,
        entityType="RiskMitigation",
        additionalInfo={"risk_id": risk_id, "status": status}
    )
    
    # Debug information
    print(f"Received update_mitigation_status request: risk_id={risk_id}, status={status}")
    print(f"Request data: {request.data}")
    
    if not risk_id:
        return Response({'error': 'Risk ID is required'}, status=400)
    
    if not status:
        return Response({'error': 'Status is required'}, status=400)
    
    try:
        # Get the risk instance
        risk_instance = RiskInstance.objects.get(RiskInstanceId=risk_id)
        
        # Update the mitigation status
        risk_instance.MitigationStatus = status
        
        # If status is completed, also update risk status to approved and set completion date
        if status == RiskInstance.MITIGATION_COMPLETED:
            risk_instance.RiskStatus = 'Approved'
            risk_instance.MitigationCompletedDate = datetime.datetime.now()
        
        risk_instance.save()
        print(f"Successfully updated risk {risk_id} mitigation status to {status}")
        
        return Response({
            'success': True,
            'message': f'Mitigation status updated to {status}'
        })
    except RiskInstance.DoesNotExist:
        print(f"Error: Risk instance with ID {risk_id} not found")
        return Response({'error': 'Risk instance not found'}, status=404)
    except Exception as e:
        print(f"Error updating mitigation status: {e}")
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@rbac_required(required_permission='view_all_risk')
def get_reviewer_comments(request, risk_id):
    """Get reviewer comments for rejected mitigations"""
    send_log(
        module="Risk",
        actionType="VIEW",
        description=f"Viewing reviewer comments for risk {risk_id}",
        userId=request.user.id if request.user.is_authenticated else None,
        userName=request.user.username if request.user.is_authenticated else None,
        entityType="RiskReview",
        additionalInfo={"risk_id": risk_id}
    )
    
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            # Get the latest R version for this risk
            cursor.execute("""
                SELECT ra.ExtractedInfo
                FROM grc.risk_approval ra
                WHERE ra.RiskInstanceId = %s 
                AND ra.version LIKE 'R%%'
                ORDER BY version DESC
                LIMIT 1
            """, [risk_id])
            
            row = cursor.fetchone()
            if not row:
                return Response({}, status=404)
            
            import json
            extracted_info = json.loads(row[0])
            
            comments = {}
            if 'mitigations' in extracted_info:
                for mitigation_id, mitigation_data in extracted_info['mitigations'].items():
                    # Only include rejected mitigations with remarks
                    if mitigation_data.get('approved') is False and mitigation_data.get('remarks'):
                        comments[mitigation_id] = mitigation_data['remarks']
            
            return Response(comments)
    except Exception as e:
        print(f"Error fetching reviewer comments: {e}")
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@rbac_required(required_permission='view_all_risk')
def get_latest_review(request, risk_id):
    """Get the latest review data for a risk (latest R version)"""
    send_log(
        module="Risk",
        actionType="VIEW",
        description=f"Viewing latest review for risk {risk_id}",
        userId=request.user.id if request.user.is_authenticated else None,
        userName=request.user.username if request.user.is_authenticated else None,
        entityType="RiskReview",
        additionalInfo={"risk_id": risk_id}
    )
    
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            # Get the latest R version of review data
            cursor.execute("""
                SELECT ExtractedInfo
                FROM grc.risk_approval
                WHERE RiskInstanceId = %s AND version LIKE 'R%%'
                ORDER BY 
                    CAST(SUBSTRING(version, 2) AS UNSIGNED) DESC
                LIMIT 1
            """, [risk_id])
            
            row = cursor.fetchone()
            if not row:
                # If no review found, return empty object
                return Response({})
            
            import json
            extracted_info = json.loads(row[0])
            print(extracted_info)
            return Response(extracted_info)
    except Exception as e:
        print(f"Error fetching latest review: {e}")
        traceback.print_exc()
        # Return empty object instead of error in case of exception
        return Response({})

@api_view(['GET'])
@rbac_required(required_permission='view_all_risk')
def get_assigned_reviewer(request, risk_id):
    """Get the assigned reviewer for a risk from the RiskInstance table's Reviewer column"""
    try:
        print(f"Looking for reviewer for risk_id: {risk_id}")
        
        with connection.cursor() as cursor:
            # First check if we have both ReviewerId and Reviewer columns populated
            cursor.execute("""
                SELECT RiskInstanceId, ReviewerId, Reviewer 
                FROM grc.risk_instance
                WHERE RiskInstanceId = %s
                LIMIT 1
            """, [risk_id])
            
            row = cursor.fetchone()
            print(f"Risk instance query result: {row}")
            
            if row:
                risk_instance_id, reviewer_id, reviewer_name = row
                print(f"Found risk instance {risk_instance_id} with reviewer_id: {reviewer_id}, reviewer_name: {reviewer_name}")
                
                # Normalize None, empty string, or 0 to None for reviewer_id
                if reviewer_id is None or reviewer_id == '' or reviewer_id == 0:
                    reviewer_id = None
                
                # Normalize empty string to None for reviewer_name
                if reviewer_name is None or reviewer_name == '':
                    reviewer_name = None
                
                # If we have both, return them
                if reviewer_id is not None and reviewer_name is not None:
                    print(f"Returning both reviewer_id and reviewer_name")
                    return Response({
                        'reviewer_id': reviewer_id,
                        'reviewer_name': reviewer_name
                    })
                
                # If we only have the name, look up the ID
                if reviewer_name is not None and reviewer_id is None:
                    print(f"Only have reviewer_name, looking up ID for: {reviewer_name}")
                    cursor.execute("""
                        SELECT UserId FROM grc.users
                        WHERE UserName = %s
                        LIMIT 1
                    """, [reviewer_name])
                    
                    id_row = cursor.fetchone()
                    if id_row:
                        reviewer_id = id_row[0]
                        print(f"Found reviewer_id: {reviewer_id} for name: {reviewer_name}")
                        
                        # Update the ReviewerId field in the risk_instance table
                        cursor.execute("""
                            UPDATE grc.risk_instance
                            SET ReviewerId = %s
                            WHERE RiskInstanceId = %s
                        """, [reviewer_id, risk_id])
                        
                        return Response({
                            'reviewer_id': reviewer_id,
                            'reviewer_name': reviewer_name
                        })
                    else:
                        print(f"Could not find reviewer_id for name: {reviewer_name}")
                        # Return just the name if we can't find the ID
                        return Response({
                            'reviewer_id': reviewer_name,  # Use name as fallback
                            'reviewer_name': reviewer_name
                        })
                
                # If we only have the ID, look up the name
                if reviewer_id is not None and reviewer_name is None:
                    print(f"Only have reviewer_id, looking up name for: {reviewer_id}")
                    cursor.execute("""
                        SELECT UserName FROM grc.users
                        WHERE UserId = %s
                        LIMIT 1
                    """, [reviewer_id])
                    
                    name_row = cursor.fetchone()
                    if name_row:
                        reviewer_name = name_row[0]
                        print(f"Found reviewer_name: {reviewer_name} for id: {reviewer_id}")
                        
                        # Update the Reviewer field in the risk_instance table
                        cursor.execute("""
                            UPDATE grc.risk_instance
                            SET Reviewer = %s
                            WHERE RiskInstanceId = %s
                        """, [reviewer_name, risk_id])
                        
                        return Response({
                            'reviewer_id': reviewer_id,
                            'reviewer_name': reviewer_name
                        })
                    else:
                        print(f"Could not find reviewer_name for id: {reviewer_id}")
                        return Response({
                            'reviewer_id': reviewer_id,
                            'reviewer_name': f"User {reviewer_id}"  # Fallback name
                        })
            
            print(f"No risk instance found for risk_id: {risk_id}")
            
            # If not found in RiskInstance, fall back to checking risk_approval table
            cursor.execute("""
                SELECT ApproverId, UserName 
                FROM grc.risk_approval ra
                JOIN grc.users u ON ra.ApproverId = u.UserId
                WHERE ra.RiskInstanceId = %s
                LIMIT 1
            """, [risk_id])
            
            row = cursor.fetchone()
            print(f"Risk approval query result: {row}")
            
            if row:
                return Response({
                    'reviewer_id': row[0],
                    'reviewer_name': row[1]
                })
                
            # If still not found, return empty object with debug info
            print(f"No reviewer found for risk_id: {risk_id}")
            return Response({
                'error': 'No reviewer assigned',
                'risk_id': risk_id,
                'message': 'No reviewer has been assigned to this risk yet'
            }, status=200)
            
    except Exception as e:
        print(f"Error fetching assigned reviewer: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        # Return error info instead of empty object
        return Response({
            'error': 'Database error',
            'message': str(e),
            'risk_id': risk_id
        }, status=200)

@csrf_exempt
@api_view(['PUT'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@rbac_required(required_permission='edit_risk')
def update_risk_mitigation(request, risk_id):
    """Update the mitigation steps for a risk instance"""
    mitigation_data = request.data.get('mitigation_data')
    
    # Log the mitigation update
    send_log(
        module="Risk",
        actionType="UPDATE_MITIGATION",
        description=f"Updating mitigation data for risk {risk_id}",
        userId=request.user.id if request.user.is_authenticated else None,
        userName=request.user.username if request.user.is_authenticated else None,
        entityType="RiskInstance",
        additionalInfo={"risk_id": risk_id}
    )
    
    if not mitigation_data:
        return Response({'error': 'Mitigation data is required'}, status=400)
    
    try:
        # Get the risk instance
        risk_instance = RiskInstance.objects.get(RiskInstanceId=risk_id)
        
        # Only update the ModifiedMitigations field, keep RiskMitigation unchanged
        risk_instance.ModifiedMitigations = mitigation_data
        risk_instance.save()
        
        return Response({
            'success': True,
            'message': 'Modified mitigation data updated successfully'
        })
    except RiskInstance.DoesNotExist:
        return Response({'error': 'Risk instance not found'}, status=404)
    except Exception as e:
        print(f"Error updating modified mitigation: {e}")
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@rbac_required(required_permission='view_all_risk')
def get_risk_form_details(request, risk_id):
    """Get form details for a risk instance"""
    try:
        risk_instance = RiskInstance.objects.get(RiskInstanceId=risk_id)
        form_details = risk_instance.RiskFormDetails
        
        # If no form details exist, return default empty structure
        if not form_details:
            form_details = {
                "cost": "",
                "impact": "",
                "recoverytime": "",
                "financialloss": "",
                "riskrecurrence": "",
                "financialimpact": "",
                "expecteddowntime": "",
                "operationalimpact": "",
                "reputationalimpact": "",
                "improvementinitiative": ""
            }
        
        return Response(form_details)
    except RiskInstance.DoesNotExist:
        return Response({"error": "Risk instance not found"}, status=404)
    except Exception as e:
        print(f"Error fetching risk form details: {e}")
        return Response({"error": str(e)}, status=500)

class GRCLogList(generics.ListCreateAPIView):
    queryset = GRCLog.objects.all().order_by('-Timestamp')
    serializer_class = GRCLogSerializer
    permission_classes = [RiskViewPermission]
    
    def get_queryset(self):
        queryset = GRCLog.objects.all().order_by('-Timestamp')
        
        # Filter by module if provided
        module = self.request.query_params.get('module')
        if module:
            queryset = queryset.filter(Module__icontains=module)
            
        # Filter by action type if provided
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(ActionType__icontains=action_type)
            
        # Filter by entity type if provided
        entity_type = self.request.query_params.get('entity_type')
        if entity_type:
            queryset = queryset.filter(EntityType__icontains=entity_type)
            
        # Filter by log level if provided
        log_level = self.request.query_params.get('log_level')
        if log_level:
            queryset = queryset.filter(LogLevel__iexact=log_level)
            
        # Filter by user if provided
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(UserId=user_id)
            
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(Timestamp__range=[start_date, end_date])
            
        return queryset

class GRCLogDetail(generics.RetrieveAPIView):
    queryset = GRCLog.objects.all()
    serializer_class = GRCLogSerializer
    permission_classes = [RiskViewPermission]

@api_view(['GET'])
@rbac_required(required_permission='view_all_risk')
def generate_test_notification(request, user_id):
    """Generate a test notification for development purposes"""
    try:
        import json
        from django.db import connection
        
        # Check if the risk_instance table exists
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = DATABASE() AND table_name = 'risk_instance'
            """)
            risk_instance_exists = cursor.fetchone()[0] > 0
            
            # If risk_instance table doesn't exist, create it
            if not risk_instance_exists:
                cursor.execute("""
                    CREATE TABLE risk_instance (
                        RiskInstanceId INT AUTO_INCREMENT PRIMARY KEY,
                        RiskId INT,
                        RiskDescription VARCHAR(255),
                        RiskStatus VARCHAR(50),
                        UserId INT
                    )
                """)
                
        # Check if the risk_approval table exists
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = DATABASE() AND table_name = 'risk_approval'
            """)
            risk_approval_exists = cursor.fetchone()[0] > 0
            
            # If risk_approval table doesn't exist, create it
            if not risk_approval_exists:
                cursor.execute("""
                    CREATE TABLE risk_approval (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        RiskInstanceId INT,
                        UserId INT,
                        ApproverId INT,
                        version VARCHAR(20),
                        ExtractedInfo TEXT,
                        ApprovedRejected VARCHAR(20)
                    )
                """)
        
        # Create a test risk instance if none exists
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM risk_instance")
            instance_count = cursor.fetchone()[0]
            
            if instance_count == 0:
                # Insert test risk instance
                cursor.execute("""
                    INSERT INTO risk_instance (RiskId, RiskDescription, RiskStatus, UserId)
                    VALUES (1, 'Test Risk for Notification', 'Under Review', %s)
                """, [user_id])
                
                # Get the newly created risk instance ID
                cursor.execute("SELECT LAST_INSERT_ID()")
                risk_instance_id = cursor.fetchone()[0]
            else:
                # Get existing risk instance ID
                cursor.execute("SELECT RiskInstanceId FROM risk_instance LIMIT 1")
                risk_instance_id = cursor.fetchone()[0]
                
                # Update the risk instance to be associated with the current user
                cursor.execute("""
                    UPDATE risk_instance 
                    SET UserId = %s
                    WHERE RiskInstanceId = %s
                """, [user_id, risk_instance_id])
        
        # Create a test approval/notification
        extracted_info = {
            "risk_id": risk_instance_id,
            "version": "R1",
            "review_date": "2023-06-01T12:00:00",
            "overall_approved": True,
            "mitigations": {
                "1": {
                    "description": "Test mitigation step",
                    "approved": True,
                    "remarks": "",
                    "comments": "Looks good"
                }
            }
        }
        
        with connection.cursor() as cursor:
            # Insert test approval record - use a simple query with the exact columns that exist
            cursor.execute("""
                INSERT INTO risk_approval 
                (RiskInstanceId, UserId, ApproverId, version, ExtractedInfo, ApprovedRejected)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [
                risk_instance_id,
                user_id,
                user_id + 1,  # Approver ID different from user ID
                "R1",
                json.dumps(extracted_info),
                "Approved"
            ])
        
        return Response({
            "success": True,
            "message": "Test notification created successfully",
            "data": {
                "risk_instance_id": risk_instance_id,
                "user_id": user_id
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            "success": False,
            "message": f"Error creating test notification: {str(e)}"
        }, status=500)


                               # KPI Views





@csrf_exempt
@api_view(['GET', 'POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])  # Temporarily allow all users for testing
def get_all_risks_for_dropdown(request):
    """
    Get all risks with essential metadata for dropdown selection
    """
    print(f"Request method: {request.method}")
    print(f"Request user: {request.user}")
    print(f"Request authenticated: {request.user.is_authenticated}")
    print(f"Request headers: {dict(request.headers)}")
    
    # Handle both GET and POST requests
    if request.method not in ['GET', 'POST']:
        return Response({"error": "Method not allowed"}, status=405)
    
    try:
        import random
        from django.db import connection
        
        # Get available departments and business units
        available_departments = []
        available_business_units = []
        
        with connection.cursor() as cursor:
            # Fetch all departments
            cursor.execute("SELECT DepartmentName FROM department WHERE DepartmentName IS NOT NULL AND DepartmentName != ''")
            available_departments = [row[0] for row in cursor.fetchall()]
            
            # Fetch all business units
            cursor.execute("SELECT Name FROM businessunits WHERE Name IS NOT NULL AND Name != ''")
            available_business_units = [row[0] for row in cursor.fetchall()]
        
        # Fallback lists if database is empty
        if not available_departments:
            available_departments = ['Core Banking IT', 'Customer Service', 'Information Security', 'Risk Management']
        
        if not available_business_units:
            available_business_units = ['Compliance Division (CD001)', 'IT Operations Unit (IT002)', 'Retail Banking (RB003)']
        
        print(f"Available Departments: {available_departments}")
        print(f"Available Business Units: {available_business_units}")
        
        # Use a more comprehensive query to get department and business unit information
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    r.RiskId,
                    r.ComplianceId,
                    r.RiskTitle,
                    r.Criticality,
                    r.PossibleDamage,
                    r.Category,
                    r.RiskType,
                    r.BusinessImpact,
                    r.RiskDescription,
                    r.RiskLikelihood,
                    r.RiskImpact,
                    r.RiskExposureRating,
                    r.RiskMultiplierX,
                    r.RiskMultiplierY,
                    r.RiskPriority,
                    r.RiskMitigation,
                    r.CreatedAt,
                    u.UserName as CreatedBy,
                    CONCAT(u.FirstName, ' ', u.LastName) as CreatedByName,
                    d.DepartmentName,
                    bu.Name as BusinessUnitName
                FROM risk r
                LEFT JOIN risk_instance ri ON r.RiskId = ri.RiskId
                LEFT JOIN users u ON ri.UserId = u.UserId
                LEFT JOIN department d ON u.DepartmentId = d.DepartmentId
                LEFT JOIN businessunits bu ON d.BusinessUnitId = bu.BusinessUnitId
                ORDER BY r.CreatedAt DESC
            """)
            
            columns = [col[0] for col in cursor.description]
            risks_data = []
            
            for row in cursor.fetchall():
                risk_dict = dict(zip(columns, row))
                # Convert datetime objects to string for JSON serialization
                if risk_dict.get('CreatedAt'):
                    if hasattr(risk_dict['CreatedAt'], 'strftime'):
                        risk_dict['CreatedAt'] = risk_dict['CreatedAt'].strftime('%Y-%m-%d %H:%M:%S')
                
                # Ensure all required fields are present with fallbacks
                risk_dict['RiskType'] = risk_dict.get('RiskType') or 'Operational'
                
                # Assign random department if missing or N/A
                if not risk_dict.get('DepartmentName') or risk_dict.get('DepartmentName') == 'N/A' or risk_dict.get('DepartmentName') is None:
                    risk_dict['DepartmentName'] = random.choice(available_departments)
                
                # Assign random business unit if missing or N/A
                if not risk_dict.get('BusinessUnitName') or risk_dict.get('BusinessUnitName') == 'N/A' or risk_dict.get('BusinessUnitName') is None:
                    risk_dict['BusinessUnitName'] = random.choice(available_business_units)
                
                # Ensure CreatedBy fields have defaults
                risk_dict['CreatedBy'] = risk_dict.get('CreatedBy') or 'System'
                risk_dict['CreatedByName'] = risk_dict.get('CreatedByName') or 'System User'
                
                risks_data.append(risk_dict)
        
        # Get framework filter info
        filter_info = get_framework_filter_info(request)
        print(f"[RISK DROPDOWN] Successfully fetched {len(risks_data)} risks with department and business unit data (filtered: {filter_info['is_filtered']})")
        
        return Response({
            'success': True,
            'risks': risks_data,
            'filter_info': filter_info
        })
    except Exception as e:
        print(f"Error fetching risks for dropdown: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([RiskViewPermission])  # RBAC: Require RiskViewPermission for viewing compliances dropdown
def get_all_compliances_for_dropdown(request, query=None):
    """
    Get all compliances with essential metadata for dropdown selection
    """
    try:
        compliances = Compliance.objects.all().order_by('ComplianceId')
        
        # Create a simplified response with only the needed fields
        compliance_data = []
        for compliance in compliances:
            compliance_data.append({
                'ComplianceId': compliance.ComplianceId,
                'ComplianceItemDescription': compliance.ComplianceItemDescription,
                'PossibleDamage': compliance.PossibleDamage,
                'Criticality': compliance.Criticality
            })
        
        return Response(compliance_data)
    except Exception as e:
        print(f"Error fetching compliances for dropdown: {e}")
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([RiskViewPermission])  # RBAC: Require RiskViewPermission for viewing users dropdown
def get_users_for_dropdown(request):
    """
    Get all users with essential metadata for dropdown selection from RBAC table
    """
    try:
        # Get users from the RBAC table with role information
        from ...models import RBAC
        rbac_users = RBAC.objects.filter(is_active='Y').order_by('username')
        
        # Create response with UserId, UserName, and Role
        user_data = []
        for rbac_user in rbac_users:
            user_data.append({
                'UserId': rbac_user.user_id,
                'UserName': rbac_user.username,
                'Role': rbac_user.role
            })
        
        return Response(user_data)
    except Exception as e:
        print(f"Error fetching users for dropdown: {e}")
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([RiskViewPermission])  # RBAC: Require RiskViewPermission for viewing business impacts
def get_business_impacts(request):
    """
    Get all business impact values from CategoryBusinessUnit
    """
    try:
        business_impacts = CategoryBusinessUnit.objects.filter(source='RiskBusinessImpact')
        return Response({
            'status': 'success',
            'data': [{'id': impact.id, 'value': impact.value} for impact in business_impacts]
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@rbac_required(required_permission='create_risk')
def add_business_impact(request):
    """
    Add a new business impact value to CategoryBusinessUnit
    """
    try:
        value = request.data.get('value')
        if not value:
            return Response({
                'status': 'error',
                'message': 'Value is required'
            }, status=400)
            
        new_impact = CategoryBusinessUnit.objects.create(
            source='RiskBusinessImpact',
            value=value
        )
        
        return Response({
            'status': 'success',
            'data': {'id': new_impact.id, 'value': new_impact.value}
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([RiskViewPermission])  # RBAC: Require RiskViewPermission for viewing departments
def get_risk_departments(request):
    """
    Fetch all departments for risk module filtering
    """
    try:
        from ...models import Department
        
        # Get all active departments
        departments = Department.objects.filter(IsActive=True).values(
            'DepartmentId', 
            'DepartmentName'
        ).order_by('DepartmentName')
        
        # Format the response
        departments_data = []
        for dept in departments:
            departments_data.append({
                'value': dept['DepartmentName'],
                'label': dept['DepartmentName']
            })
        
        return Response({
            'success': True,
            'departments': departments_data
        })
        
    except Exception as e:
        print(f"Error fetching departments: {str(e)}")
        return Response({
            'success': False,
            'error': f'Failed to fetch departments: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([RiskViewPermission])  # RBAC: Require RiskViewPermission for viewing business units
def get_risk_business_units(request):
    """
    Fetch all business units for risk module filtering
    """
    try:
        from ...models import BusinessUnit
        
        # Get all active business units
        business_units = BusinessUnit.objects.filter(IsActive=True).values(
            'BusinessUnitId', 
            'Name',
            'Code'
        ).order_by('Name')
        
        # Format the response
        business_units_data = []
        for bu in business_units:
            business_units_data.append({
                'value': bu['Name'],
                'label': f"{bu['Name']} ({bu['Code']})"
            })
        
        return Response({
            'success': True,
            'business_units': business_units_data
        })
        
    except Exception as e:
        print(f"Error fetching business units: {str(e)}")
        return Response({
            'success': False,
            'error': f'Failed to fetch business units: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([RiskViewPermission])  # RBAC: Require RiskViewPermission for viewing risk categories
def get_risk_categories(request):
    """
    Get all risk category values from CategoryBusinessUnit
    """
    try:
        categories = CategoryBusinessUnit.objects.filter(source='RiskCategory')
        return Response({
            'status': 'success',
            'data': [{'id': category.id, 'value': category.value} for category in categories]
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@rbac_required(required_permission='create_risk')
def add_risk_category(request):
    """
    Add a new risk category value to CategoryBusinessUnit
    """
    try:
        value = request.data.get('value')
        if not value:
            return Response({
                'status': 'error',
                'message': 'Value is required'
            }, status=400)
            
        new_category = CategoryBusinessUnit.objects.create(
            source='RiskCategory',
            value=value
        )
        
        return Response({
            'status': 'success',
            'data': {'id': new_category.id, 'value': new_category.value}
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)




@api_view(['GET'])
@rbac_required(required_permission='risk_performance_analytics')
def get_risk_heatmap_data(request):
    """Get risk heatmap data showing count of risks by impact and likelihood with filters"""
    try:
        print("=== FETCHING RISK HEATMAP DATA ===")
        
        # Get filter parameters
        framework_id = request.GET.get('framework_id')
        policy_id = request.GET.get('policy_id')
        time_range = request.GET.get('timeRange', 'all')
        category = request.GET.get('category', 'all')
        priority = request.GET.get('priority', 'all')
        
        print(f"Heatmap Filters - Framework: {framework_id}, Policy: {policy_id}, Time: {time_range}, Category: {category}, Priority: {priority}")
        
        # Start with base queryset
        queryset = RiskInstance.objects.filter(
            RiskImpact__isnull=False,
            RiskLikelihood__isnull=False
        )
        
        # Apply framework filter - RiskInstance has direct ForeignKey to Framework
        if framework_id and framework_id != 'all':
            queryset = queryset.filter(FrameworkId=framework_id)
            print(f"Applied framework filter: {framework_id}")
        
        # Apply policy filter - Need to filter through ComplianceId
        if policy_id and policy_id != 'all':
            from grc.models import Policy, SubPolicy, Compliance
            try:
                policy = Policy.objects.get(PolicyId=policy_id)
                subpolicy_ids = SubPolicy.objects.filter(PolicyId=policy).values_list('SubPolicyId', flat=True)
                compliance_ids = Compliance.objects.filter(SubPolicyId__in=subpolicy_ids).values_list('ComplianceId', flat=True)
                queryset = queryset.filter(ComplianceId__in=compliance_ids)
                print(f"Applied policy filter: {policy.PolicyName}")
            except Policy.DoesNotExist:
                print(f"Policy with ID {policy_id} not found")
        
        # Apply time range filter
        if time_range != 'all':
            from django.utils import timezone
            from datetime import timedelta
            end_date = timezone.now()
            if time_range == '30days':
                start_date = end_date - timedelta(days=30)
            elif time_range == '90days':
                start_date = end_date - timedelta(days=90)
            elif time_range == '6months':
                start_date = end_date - timedelta(days=180)
            elif time_range == '1year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=180)
            queryset = queryset.filter(CreatedAt__gte=start_date, CreatedAt__lte=end_date)
            print(f"Applied time filter: {time_range}")
        
        # Apply category filter
        if category and category != 'all':
            queryset = queryset.filter(Category=category)
            print(f"Applied category filter: {category}")
        
        # Apply priority filter
        if priority and priority != 'all':
            queryset = queryset.filter(RiskPriority=priority)
            print(f"Applied priority filter: {priority}")
        
        # Query filtered risks
        risks = queryset.values('RiskImpact', 'RiskLikelihood')
       
        print(f"Total risks found after filtering: {len(risks)}")
       
        # Initialize 10x10 matrix with zeros
        heatmap_data = [[0 for _ in range(10)] for _ in range(10)]
       
        # Count risks for each impact-likelihood combination
        for risk in risks:
            impact = risk['RiskImpact']
            likelihood = risk['RiskLikelihood']
            print(f"Processing risk - Impact: {impact}, Likelihood: {likelihood}")
           
            # Ensure values are within 1-10 range
            if 1 <= impact <= 10 and 1 <= likelihood <= 10:
                impact_idx = impact - 1  # Convert to 0-based index
                likelihood_idx = likelihood - 1  # Convert to 0-based index
                heatmap_data[impact_idx][likelihood_idx] += 1
            else:
                print(f"Warning: Invalid values - Impact: {impact}, Likelihood: {likelihood}")
       
        # Print the final heatmap matrix
        print("\nHeatmap Matrix:")
        for i, row in enumerate(heatmap_data):
            print(f"Impact {i+1}: {row}")
       
        return Response({
            'heatmap_data': heatmap_data,
            'total_risks': len(risks)
        })
    except Exception as e:
        print(f"Error generating risk heatmap data: {e}")
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
@rbac_required(required_permission='risk_performance_analytics')
def get_risks_by_heatmap_coordinates(request, impact, likelihood):
    """
    Get all risk instances for a specific impact-likelihood combination with filters
    """
    try:
        print(f"=== FETCHING RISKS BY HEATMAP COORDINATES ===")
        print(f"Impact: {impact}, Likelihood: {likelihood}")
        
        # Get filter parameters
        framework_id = request.GET.get('framework_id')
        policy_id = request.GET.get('policy_id')
        time_range = request.GET.get('timeRange', 'all')
        category = request.GET.get('category', 'all')
        priority = request.GET.get('priority', 'all')
        
        print(f"Filters - Framework: {framework_id}, Policy: {policy_id}, Time: {time_range}, Category: {category}, Priority: {priority}")
        
        # Start with base queryset
        queryset = RiskInstance.objects.filter(
            RiskImpact=impact,
            RiskLikelihood=likelihood
        )
        
        # Apply framework filter - RiskInstance has direct ForeignKey to Framework
        if framework_id and framework_id != 'all':
            queryset = queryset.filter(FrameworkId=framework_id)
            print(f"Applied framework filter: {framework_id}")
        
        # Apply policy filter - Need to filter through ComplianceId
        if policy_id and policy_id != 'all':
            from grc.models import Policy, SubPolicy, Compliance
            try:
                policy = Policy.objects.get(PolicyId=policy_id)
                subpolicy_ids = SubPolicy.objects.filter(PolicyId=policy).values_list('SubPolicyId', flat=True)
                compliance_ids = Compliance.objects.filter(SubPolicyId__in=subpolicy_ids).values_list('ComplianceId', flat=True)
                queryset = queryset.filter(ComplianceId__in=compliance_ids)
                print(f"Applied policy filter: {policy.PolicyName}")
            except Policy.DoesNotExist:
                print(f"Policy with ID {policy_id} not found")
        
        # Apply time range filter
        if time_range != 'all':
            from django.utils import timezone
            from datetime import timedelta
            end_date = timezone.now()
            if time_range == '30days':
                start_date = end_date - timedelta(days=30)
            elif time_range == '90days':
                start_date = end_date - timedelta(days=90)
            elif time_range == '6months':
                start_date = end_date - timedelta(days=180)
            elif time_range == '1year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=180)
            queryset = queryset.filter(CreatedAt__gte=start_date, CreatedAt__lte=end_date)
            print(f"Applied time filter: {time_range}")
        
        # Apply category filter
        if category and category != 'all':
            queryset = queryset.filter(Category=category)
            print(f"Applied category filter: {category}")
        
        # Apply priority filter
        if priority and priority != 'all':
            queryset = queryset.filter(RiskPriority=priority)
            print(f"Applied priority filter: {priority}")
        
        # Serialize the queryset
        from ...serializers import RiskInstanceSerializer
        risk_instances = queryset.order_by('-CreatedAt')
        serializer = RiskInstanceSerializer(risk_instances, many=True)
        
        print(f"Found {len(serializer.data)} risks for Impact {impact}, Likelihood {likelihood}")
        
        return Response({
            'status': 'success',
            'impact': impact,
            'likelihood': likelihood,
            'count': len(serializer.data),
            'risks': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error fetching risks by heatmap coordinates Impact {impact}, Likelihood {likelihood}: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Error fetching risks for Impact {impact}, Likelihood {likelihood}',
            'error': str(e)
        }, status=500)
 
@api_view(['GET'])
@rbac_required(required_permission='risk_performance_analytics')
def risk_trend_over_time(request):
    """
    Get risk trend data over time showing new risks and mitigated risks with filters
    """
    try:
        print("\n=== RISK TREND OVER TIME DEBUG ===")
        print("1. Request Parameters:")
        print(f"   - Query Params: {request.GET}")
       
        # Get filter parameters
        framework_id = request.GET.get('framework_id')
        policy_id = request.GET.get('policy_id')
        time_range = request.GET.get('timeRange', '6months')
        category = request.GET.get('category', 'all')
        priority = request.GET.get('priority', 'all')
        
        print(f"   - Framework: {framework_id}")
        print(f"   - Policy: {policy_id}")
        print(f"   - Time Range: {time_range}")
        print(f"   - Category: {category}")
        print(f"   - Priority: {priority}")
       
        # Define the time period to analyze
        today = timezone.now().date()
        if time_range == '30days':
            start_date = today - timedelta(days=30)
        elif time_range == '90days':
            start_date = today - timedelta(days=90)
        elif time_range == '6months':
            start_date = today - timedelta(days=180)
        elif time_range == '1year':
            start_date = today - timedelta(days=365)
        else:
            start_date = today - timedelta(days=180)
       
        print("\n2. Date Range:")
        print(f"   - Start Date: {start_date}")
        print(f"   - End Date: {today}")
       
        # Base queryset for new risks
        new_risks_queryset = RiskInstance.objects.filter(
            CreatedAt__gte=start_date,
            CreatedAt__lte=today
        )
        print("\n3. Initial Query Counts:")
        print(f"   - Total Risk Instances: {RiskInstance.objects.all().count()}")
        print(f"   - Filtered by Date Range: {new_risks_queryset.count()}")
       
        # Base queryset for mitigated risks
        mitigated_risks_queryset = RiskInstance.objects.filter(
            MitigationStatus=RiskInstance.MITIGATION_COMPLETED,
            MitigationCompletedDate__isnull=False,
            MitigationCompletedDate__gte=start_date,
            MitigationCompletedDate__lte=today
        )
        print(f"   - Total Mitigated Risks: {mitigated_risks_queryset.count()}")
       
        # Apply framework filter - RiskInstance has direct ForeignKey to Framework
        if framework_id and framework_id != 'all':
            new_risks_queryset = new_risks_queryset.filter(FrameworkId=framework_id)
            mitigated_risks_queryset = mitigated_risks_queryset.filter(FrameworkId=framework_id)
            print(f"\n4. Framework Filter Applied: {framework_id}")
            print(f"   - Filtered New Risks Count: {new_risks_queryset.count()}")
            print(f"   - Filtered Mitigated Risks Count: {mitigated_risks_queryset.count()}")
        
        # Apply policy filter - Need to filter through ComplianceId
        if policy_id and policy_id != 'all':
            from grc.models import Policy, SubPolicy, Compliance
            try:
                policy = Policy.objects.get(PolicyId=policy_id)
                subpolicy_ids = SubPolicy.objects.filter(PolicyId=policy).values_list('SubPolicyId', flat=True)
                compliance_ids = Compliance.objects.filter(SubPolicyId__in=subpolicy_ids).values_list('ComplianceId', flat=True)
                new_risks_queryset = new_risks_queryset.filter(ComplianceId__in=compliance_ids)
                mitigated_risks_queryset = mitigated_risks_queryset.filter(ComplianceId__in=compliance_ids)
                print(f"\n5. Policy Filter Applied: {policy.PolicyName}")
                print(f"   - Filtered New Risks Count: {new_risks_queryset.count()}")
                print(f"   - Filtered Mitigated Risks Count: {mitigated_risks_queryset.count()}")
            except Policy.DoesNotExist:
                print(f"\nERROR: Policy with id {policy_id} not found")
       
        # Apply category filter if specified
        if category and category.lower() != 'all':
            try:
                category_obj = CategoryBusinessUnit.objects.get(id=category)
                db_category = category_obj.value
                print(f"\n6. Category Filter Applied: {db_category}")
                new_risks_queryset = new_risks_queryset.filter(Category__iexact=db_category)
                mitigated_risks_queryset = mitigated_risks_queryset.filter(Category__iexact=db_category)
                print(f"   - Filtered New Risks Count: {new_risks_queryset.count()}")
                print(f"   - Filtered Mitigated Risks Count: {mitigated_risks_queryset.count()}")
            except CategoryBusinessUnit.DoesNotExist:
                print(f"\nERROR: Category with id {category} not found")
                return JsonResponse({
                    'error': f'Category with id {category} not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Apply priority filter
        if priority and priority != 'all':
            new_risks_queryset = new_risks_queryset.filter(RiskPriority=priority)
            mitigated_risks_queryset = mitigated_risks_queryset.filter(RiskPriority=priority)
            print(f"\n7. Priority Filter Applied: {priority}")
            print(f"   - Filtered New Risks Count: {new_risks_queryset.count()}")
            print(f"   - Filtered Mitigated Risks Count: {mitigated_risks_queryset.count()}")
       
        # Generate monthly data points
        months = []
        new_risks_data = []
        mitigated_risks_data = []
       
        print("\n5. Monthly Data Generation:")
        current_date = start_date
        while current_date <= today:
            month_start = current_date.replace(day=1)
            if current_date.month == 12:
                month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
           
            # Count new risks for this month
            new_count = new_risks_queryset.filter(
                CreatedAt__gte=month_start,
                CreatedAt__lte=month_end
            ).count()
           
            # Count mitigated risks for this month
            mitigated_count = mitigated_risks_queryset.filter(
                MitigationCompletedDate__gte=month_start,
                MitigationCompletedDate__lte=month_end
            ).count()
           
            month_label = month_start.strftime('%b %Y')
            months.append(month_label)
            new_risks_data.append(new_count)
            mitigated_risks_data.append(mitigated_count)
           
            print(f"   Month: {month_label}")
            print(f"   - New Risks: {new_count}")
            print(f"   - Mitigated: {mitigated_count}")
           
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
       
        # Calculate percentage changes
        new_risks_change = 0
        mitigated_risks_change = 0
       
        if len(new_risks_data) >= 2:
            prev_new = new_risks_data[-2] if new_risks_data[-2] > 0 else 1
            new_risks_change = round(((new_risks_data[-1] - new_risks_data[-2]) / prev_new) * 100, 1)
           
            prev_mitigated = mitigated_risks_data[-2] if mitigated_risks_data[-2] > 0 else 1
            mitigated_risks_change = round(((mitigated_risks_data[-1] - mitigated_risks_data[-2]) / prev_mitigated) * 100, 1)
       
        print("\n6. Percentage Changes:")
        print(f"   - New Risks Change: {new_risks_change}%")
        print(f"   - Mitigated Risks Change: {mitigated_risks_change}%")
       
        # Get available categories
        categories = CategoryBusinessUnit.objects.filter(source='risk').values('id', 'value')
        print(f"\n7. Available Categories: {list(categories)}")
       
        response_data = {
            'months': months,
            'newRisks': {
                'data': new_risks_data,
                'percentageChange': new_risks_change
            },
            'mitigatedRisks': {
                'data': mitigated_risks_data,
                'percentageChange': mitigated_risks_change
            },
            'period': time_range,
            'categories': list(categories)
        }
       
        print("\n8. Final Response Data:")
        print(json.dumps(response_data, indent=2))
        print("\n=== END RISK TREND OVER TIME DEBUG ===\n")
       
        return JsonResponse(response_data)
       
    except Exception as e:
        import traceback
        print("\nERROR in risk_trend_over_time:")
        print(f"Exception: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())
        return JsonResponse({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['GET'])
@rbac_required(required_permission='risk_performance_analytics')
def get_risks_by_category(request, category):
    """
    Get all risk instances for a specific category
    """
    try:
        # Use raw SQL query to avoid ORM date conversion issues
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    ri.*,
                    u.UserName as CreatedBy,
                    CONCAT(u.FirstName, ' ', u.LastName) as CreatedByName,
                    d.DepartmentName,
                    bu.Name as BusinessUnitName
                FROM risk_instance ri
                LEFT JOIN users u ON ri.UserId = u.UserId
                LEFT JOIN department d ON u.DepartmentId = d.DepartmentId
                LEFT JOIN businessunits bu ON d.BusinessUnitId = bu.BusinessUnitId
                WHERE ri.Category = %s
                ORDER BY ri.CreatedAt DESC
            """, [category])
            
            columns = [col[0] for col in cursor.description]
            risk_instances_data = []
            
            for row in cursor.fetchall():
                # Convert row to dictionary
                instance_dict = dict(zip(columns, row))
                
                # Convert date objects to string to avoid utcoffset error
                if 'MitigationDueDate' in instance_dict and instance_dict['MitigationDueDate']:
                    instance_dict['MitigationDueDate'] = instance_dict['MitigationDueDate'].isoformat()
                
                if 'CreatedAt' in instance_dict and instance_dict['CreatedAt']:
                    instance_dict['CreatedAt'] = instance_dict['CreatedAt'].isoformat()
                
                if 'MitigationCompletedDate' in instance_dict and instance_dict['MitigationCompletedDate']:
                    instance_dict['MitigationCompletedDate'] = instance_dict['MitigationCompletedDate'].isoformat()
                
                risk_instances_data.append(instance_dict)
        
        return Response({
            'status': 'success',
            'category': category,
            'count': len(risk_instances_data),
            'risks': risk_instances_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching risks by category {category}: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Error fetching risks for category {category}',
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@rbac_required(required_permission='risk_performance_analytics')
def custom_risk_analysis(request):
    """
    Endpoint to provide dynamic data for the Custom Risk Analysis chart
    based on selected X and Y axes.
    """
    print("==== CUSTOM RISK ANALYSIS ENDPOINT CALLED ====")
   
    # Get parameters from request
    x_axis = request.GET.get('x_axis', 'category')
    y_axis = request.GET.get('y_axis', 'exposure')
    time_range = request.GET.get('timeRange', '6months')
    category_filter = request.GET.get('category', 'all')
    priority_filter = request.GET.get('priority', 'all')
   
    print(f"Parameters: x_axis={x_axis}, y_axis={y_axis}, timeRange={time_range}, category={category_filter}, priority={priority_filter}")
   
    # Define time period based on time_range
    today = timezone.now().date()
    if time_range == '30days':
        start_date = today - timedelta(days=30)
    elif time_range == '90days':
        start_date = today - timedelta(days=90)
    elif time_range == '1year':
        start_date = today - timedelta(days=365)
    else:  # Default to 6 months
        start_date = today - timedelta(days=180)
   
    # Start with base queryset - apply framework filtering
    queryset = apply_framework_filter_to_risk_instances(
        RiskInstance.objects.filter(CreatedAt__gte=start_date), 
        request
    )
   
    # Apply filters if specified
    if category_filter and category_filter.lower() != 'all':
        try:
            category_obj = CategoryBusinessUnit.objects.get(id=category_filter)
            db_category = category_obj.value
            queryset = queryset.filter(Category__iexact=db_category)
        except CategoryBusinessUnit.DoesNotExist:
            return JsonResponse({
                'error': f'Category with id {category_filter} not found'
            }, status=status.HTTP_404_NOT_FOUND)
   
    if priority_filter and priority_filter.lower() != 'all':
        queryset = queryset.filter(RiskPriority__iexact=priority_filter)
   
    # Fetch data based on X-axis selection
    labels = []
    datasets = []
   
    try:
        # Process data based on X-axis selection
        if x_axis == 'category':
            # Group by Category
            category_data = queryset.values('Category').annotate(
                count=models.Count('RiskInstanceId'),
                avg_exposure=models.Avg('RiskExposureRating'),
                avg_impact=models.Avg('RiskImpact'),
                avg_likelihood=models.Avg('RiskLikelihood')
            ).order_by('Category')
           
            labels = [item['Category'] if item['Category'] else 'Uncategorized' for item in category_data]
           
            # Get Y-axis data
            if y_axis == 'count':
                data = [item['count'] for item in category_data]
            elif y_axis == 'exposure':
                data = [float(item['avg_exposure'] or 0) for item in category_data]
            elif y_axis == 'impact':
                data = [float(item['avg_impact'] or 0) for item in category_data]
            elif y_axis == 'likelihood':
                data = [float(item['avg_likelihood'] or 0) for item in category_data]
            else:
                data = [item['count'] for item in category_data]  # Default to count
               
        elif x_axis == 'priority':
            # Group by RiskPriority
            priority_data = queryset.values('RiskPriority').annotate(
                count=models.Count('RiskInstanceId'),
                avg_exposure=models.Avg('RiskExposureRating'),
                avg_impact=models.Avg('RiskImpact'),
                avg_likelihood=models.Avg('RiskLikelihood')
            ).order_by('RiskPriority')
           
            labels = [item['RiskPriority'] if item['RiskPriority'] else 'Unspecified' for item in priority_data]
           
            # Get Y-axis data
            if y_axis == 'count':
                data = [item['count'] for item in priority_data]
            elif y_axis == 'exposure':
                data = [float(item['avg_exposure'] or 0) for item in priority_data]
            elif y_axis == 'impact':
                data = [float(item['avg_impact'] or 0) for item in priority_data]
            elif y_axis == 'likelihood':
                data = [float(item['avg_likelihood'] or 0) for item in priority_data]
            else:
                data = [item['count'] for item in priority_data]  # Default to count
               
        elif x_axis == 'criticality':
            # Group by Criticality
            criticality_data = queryset.values('Criticality').annotate(
                count=models.Count('RiskInstanceId'),
                avg_exposure=models.Avg('RiskExposureRating'),
                avg_impact=models.Avg('RiskImpact'),
                avg_likelihood=models.Avg('RiskLikelihood')
            ).order_by('Criticality')
           
            labels = [item['Criticality'] if item['Criticality'] else 'Unspecified' for item in criticality_data]
           
            # Get Y-axis data
            if y_axis == 'count':
                data = [item['count'] for item in criticality_data]
            elif y_axis == 'exposure':
                data = [float(item['avg_exposure'] or 0) for item in criticality_data]
            elif y_axis == 'impact':
                data = [float(item['avg_impact'] or 0) for item in criticality_data]
            elif y_axis == 'likelihood':
                data = [float(item['avg_likelihood'] or 0) for item in criticality_data]
            else:
                data = [item['count'] for item in criticality_data]  # Default to count
               
        elif x_axis == 'status':
            # Group by RiskStatus
            status_data = queryset.values('RiskStatus').annotate(
                count=models.Count('RiskInstanceId'),
                avg_exposure=models.Avg('RiskExposureRating'),
                avg_impact=models.Avg('RiskImpact'),
                avg_likelihood=models.Avg('RiskLikelihood')
            ).order_by('RiskStatus')
           
            labels = [item['RiskStatus'] if item['RiskStatus'] else 'Unspecified' for item in status_data]
           
            # Get Y-axis data
            if y_axis == 'count':
                data = [item['count'] for item in status_data]
            elif y_axis == 'exposure':
                data = [float(item['avg_exposure'] or 0) for item in status_data]
            elif y_axis == 'impact':
                data = [float(item['avg_impact'] or 0) for item in status_data]
            elif y_axis == 'likelihood':
                data = [float(item['avg_likelihood'] or 0) for item in status_data]
            else:
                data = [item['count'] for item in status_data]  # Default to count
               
        elif x_axis == 'appetite':
            # Group by Appetite
            appetite_data = queryset.values('Appetite').annotate(
                count=models.Count('RiskInstanceId'),
                avg_exposure=models.Avg('RiskExposureRating'),
                avg_impact=models.Avg('RiskImpact'),
                avg_likelihood=models.Avg('RiskLikelihood')
            ).order_by('Appetite')
           
            labels = [item['Appetite'] if item['Appetite'] else 'Unspecified' for item in appetite_data]
           
            # Get Y-axis data
            if y_axis == 'count':
                data = [item['count'] for item in appetite_data]
            elif y_axis == 'exposure':
                data = [float(item['avg_exposure'] or 0) for item in appetite_data]
            elif y_axis == 'impact':
                data = [float(item['avg_impact'] or 0) for item in appetite_data]
            elif y_axis == 'likelihood':
                data = [float(item['avg_likelihood'] or 0) for item in appetite_data]
            else:
                data = [item['count'] for item in appetite_data]  # Default to count
               
        elif x_axis == 'mitigation':
            # Group by MitigationStatus
            mitigation_data = queryset.values('MitigationStatus').annotate(
                count=models.Count('RiskInstanceId'),
                avg_exposure=models.Avg('RiskExposureRating'),
                avg_impact=models.Avg('RiskImpact'),
                avg_likelihood=models.Avg('RiskLikelihood')
            ).order_by('MitigationStatus')
           
            labels = [item['MitigationStatus'] if item['MitigationStatus'] else 'Unspecified' for item in mitigation_data]
           
            # Get Y-axis data
            if y_axis == 'count':
                data = [item['count'] for item in mitigation_data]
            elif y_axis == 'exposure':
                data = [float(item['avg_exposure'] or 0) for item in mitigation_data]
            elif y_axis == 'impact':
                data = [float(item['avg_impact'] or 0) for item in mitigation_data]
            elif y_axis == 'likelihood':
                data = [float(item['avg_likelihood'] or 0) for item in mitigation_data]
            else:
                data = [item['count'] for item in mitigation_data]  # Default to count
               
        else:
            # Default to time-based analysis (last 7 days)
            date_range = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
            labels = [(today - timedelta(days=i)).strftime('%b %d') for i in range(6, -1, -1)]
           
            # Get counts for each day
            time_data = {}
            for date_str in date_range:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                day_queryset = queryset.filter(CreatedAt=date_obj)
               
                if y_axis == 'count':
                    time_data[date_str] = day_queryset.count()
                elif y_axis == 'exposure':
                    avg_exposure = day_queryset.aggregate(avg=models.Avg('RiskExposureRating'))['avg'] or 0
                    time_data[date_str] = float(avg_exposure)
                elif y_axis == 'impact':
                    avg_impact = day_queryset.aggregate(avg=models.Avg('RiskImpact'))['avg'] or 0
                    time_data[date_str] = float(avg_impact)
                elif y_axis == 'likelihood':
                    avg_likelihood = day_queryset.aggregate(avg=models.Avg('RiskLikelihood'))['avg'] or 0
                    time_data[date_str] = float(avg_likelihood)
                else:
                    time_data[date_str] = day_queryset.count()  # Default to count
           
            data = [time_data.get(date_str, 0) for date_str in date_range]
       
        # Create datasets based on Y-axis
        if y_axis == 'count':
            datasets = [{
                'label': 'Risk Count',
                'data': data,
                'backgroundColor': '#4f6cff',
                'borderColor': '#4f6cff'
            }]
        elif y_axis == 'exposure':
            datasets = [{
                'label': 'Risk Exposure Rating',
                'data': data,
                'backgroundColor': '#f87171',
                'borderColor': '#f87171'
            }]
        elif y_axis == 'impact':
            datasets = [{
                'label': 'Risk Impact',
                'data': data,
                'backgroundColor': '#fbbf24',
                'borderColor': '#fbbf24'
            }]
        elif y_axis == 'likelihood':
            datasets = [{
                'label': 'Risk Likelihood',
                'data': data,
                'backgroundColor': '#4ade80',
                'borderColor': '#4ade80'
            }]
        else:
            # Default
            datasets = [{
                'label': 'Count',
                'data': data,
                'backgroundColor': '#4f6cff',
                'borderColor': '#4f6cff'
            }]
       
        # For stacked bar chart, add additional datasets
        if y_axis == 'count' and x_axis in ['category', 'priority', 'criticality', 'status', 'appetite', 'mitigation']:
            # Get priority distribution for each group
            high_priority = []
            medium_priority = []
            low_priority = []
           
            for label in labels:
                field_name = x_axis.capitalize() if x_axis != 'mitigation' else 'MitigationStatus'
               
                # Skip if label is 'Unspecified' or 'Uncategorized'
                if label in ['Unspecified', 'Uncategorized']:
                    filter_args = {f"{field_name}__isnull": True}
                else:
                    filter_args = {f"{field_name}__iexact": label}
               
                group_queryset = queryset.filter(**filter_args)
               
                high_count = group_queryset.filter(RiskPriority__iexact='High').count()
                medium_count = group_queryset.filter(RiskPriority__iexact='Medium').count()
                low_count = group_queryset.filter(RiskPriority__iexact='Low').count()
               
                high_priority.append(high_count)
                medium_priority.append(medium_count)
                low_priority.append(low_count)
           
            # Replace single dataset with stacked datasets
            datasets = [
                {
                    'label': 'High',
                    'data': high_priority,
                    'backgroundColor': '#f87171',  # Red
                    'stack': 'Stack 0',
                    'borderRadius': 4
                },
                {
                    'label': 'Medium',
                    'data': medium_priority,
                    'backgroundColor': '#fbbf24',  # Yellow
                    'stack': 'Stack 0',
                    'borderRadius': 4
                },
                {
                    'label': 'Low',
                    'data': low_priority,
                    'backgroundColor': '#4ade80',  # Green
                    'stack': 'Stack 0',
                    'borderRadius': 4
                }
            ]
       
        # Return the chart data
        response_data = {
            'labels': labels,
            'datasets': datasets,
            'xAxis': x_axis,
            'yAxis': y_axis
        }
       
        return JsonResponse(response_data)
       
    except Exception as e:
        print(f"Error in custom_risk_analysis: {str(e)}")
        traceback.print_exc()
        return JsonResponse({
            'error': str(e),
            'message': 'An error occurred while processing risk analysis data'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([RiskAnalyticsPermission])  # RBAC: Require RiskAnalyticsPermission for viewing risk metrics
def risk_metrics(request):
    """
    Get risk metrics with optional time filter
    """
    time_range = request.GET.get('timeRange', 'all')
    category = request.GET.get('category', 'all')
    priority = request.GET.get('priority', 'all')
   
    print(f"FILTER REQUEST: timeRange={time_range}, category={category}, priority={priority}")
   
    # Start with all risk instances
    queryset = RiskInstance.objects.all()
    print(f"Initial queryset count: {queryset.count()}")
   
    # Print columns and raw data for debugging
    print("Available columns:", [f.name for f in RiskInstance._meta.fields])
   
    # Sample data dump for debugging (first 5 records)
    print("Sample data:")
    for instance in queryset[:5]:
        print(f"ID: {instance.RiskInstanceId}, Category: {instance.Category}, Priority: {instance.RiskPriority}, Status: {instance.RiskStatus}")
   
    # Apply time filter if not 'all'
    if time_range != 'all':
        today = timezone.now().date()
        if time_range == '7days':
            start_date = today - timedelta(days=7)
        elif time_range == '30days':
            start_date = today - timedelta(days=30)
        elif time_range == '90days':
            start_date = today - timedelta(days=90)
        elif time_range == '6months':
            start_date = today - timedelta(days=180)
        elif time_range == '1year':
            start_date = today - timedelta(days=365)
        else:
            start_date = None
           
        if start_date:
            queryset = queryset.filter(CreatedAt__gte=start_date)
            print(f"After time filter ({time_range}): {queryset.count()} records")
   
    # Apply category filter if not 'all'
    if category != 'all':
        # Handle the case conversion between frontend and backend naming
        category_map = {
            'operational': 'Operational',
            'financial': 'Financial',
            'strategic': 'Strategic',
            'compliance': 'Compliance',
            'it-security': 'IT Security'
        }
        db_category = category_map.get(category, category)
        queryset = queryset.filter(Category__iexact=db_category)
        print(f"After category filter ({db_category}): {queryset.count()} records")
   
    # Apply priority filter if not 'all'
    if priority != 'all':
        # Handle the case conversion between frontend and backend naming
        priority_map = {
            'critical': 'Critical',
            'high': 'High',
            'medium': 'Medium',
            'low': 'Low'
        }
        db_priority = priority_map.get(priority, priority)
        queryset = queryset.filter(RiskPriority__iexact=db_priority)
        print(f"After priority filter ({db_priority}): {queryset.count()} records")
   
    # Calculate metrics
    total_risks = queryset.count()
    print(f"Final filtered count: {total_risks} records")
   
    # Accepted risks: Count risks with RiskStatus "Assigned" or "Approved"
    accepted_risks = queryset.filter(
        Q(RiskStatus__iexact='Assigned') | Q(RiskStatus__iexact='Approved')
    ).count()
    print(f"Accepted risks (Assigned or Approved): {accepted_risks}")
   
    # Rejected risks: Count risks with RiskStatus "Rejected"
    rejected_risks = queryset.filter(RiskStatus__iexact='Rejected').count()
    print(f"Rejected risks: {rejected_risks}")
 
    # Mitigated risks: Count rows with "Completed" in MitigationStatus
    mitigated_risks = 0
    in_progress_risks = 0
   
    # Print all distinct RiskStatus values to help debugging
    statuses = queryset.values_list('RiskStatus', flat=True).distinct()
    print(f"All RiskStatus values in filtered data: {list(statuses)}")
   
    try:
        # First try directly with ORM if MitigationStatus field exists
        if 'MitigationStatus' in [f.name for f in RiskInstance._meta.fields]:
            print("Trying ORM for MitigationStatus counts")
            mitigated_risks = queryset.filter(MitigationStatus=RiskInstance.MITIGATION_COMPLETED).count()
            in_progress_risks = queryset.filter(MitigationStatus=RiskInstance.MITIGATION_IN_PROGRESS).count()
            print(f"ORM counts - Mitigated: {mitigated_risks}, In Progress: {in_progress_risks}")
       
        # If that doesn't work or returns 0, try with direct SQL
        if mitigated_risks == 0 and in_progress_risks == 0:
            print("Trying direct SQL for MitigationStatus counts")
            with connection.cursor() as cursor:
                # First create a list of all the IDs from the queryset to use in our SQL
                risk_ids = list(queryset.values_list('RiskInstanceId', flat=True))
               
                if risk_ids:
                    # Convert the list to a comma-separated string for SQL
                    risk_ids_str = ','.join(map(str, risk_ids))
                   
                    # Check if MitigationStatus column exists
                    cursor.execute("SHOW COLUMNS FROM risk_instance LIKE 'MitigationStatus'")
                    mitigation_status_exists = cursor.fetchone() is not None
                    print(f"MitigationStatus column exists: {mitigation_status_exists}")
                   
                    if mitigation_status_exists:
                        # Count mitigated risks
                        sql = f"SELECT COUNT(*) FROM risk_instance WHERE RiskInstanceId IN ({risk_ids_str}) AND MitigationStatus = 'Completed'"
                        print(f"Executing SQL: {sql}")
                        cursor.execute(sql)
                        row = cursor.fetchone()
                        mitigated_risks = row[0] if row else 0
                       
                        # Count in-progress risks
                        sql = f"SELECT COUNT(*) FROM risk_instance WHERE RiskInstanceId IN ({risk_ids_str}) AND MitigationStatus = 'Work in Progress'"
                        print(f"Executing SQL: {sql}")
                        cursor.execute(sql)
                        row = cursor.fetchone()
                        in_progress_risks = row[0] if row else 0
                       
                        print(f"SQL counts - Mitigated: {mitigated_risks}, In Progress: {in_progress_risks}")
    except Exception as e:
        print(f"Error getting mitigated/in-progress risks: {e}")
   
    response_data = {
        'total': total_risks,
        'accepted': accepted_risks,
        'rejected': rejected_risks,
        'mitigated': mitigated_risks,
        'inProgress': in_progress_risks
    }
    print(f"Final response: {response_data}")
   
    return Response(response_data)
 
 
 
 
 
@api_view(['GET'])
@permission_classes([RiskAnalyticsPermission])  # RBAC: Require RiskAnalyticsPermission for viewing risk metrics by category
def risk_metrics_by_category(request):
    # Get filter parameters
    framework_id = request.GET.get('framework_id')
    policy_id = request.GET.get('policy_id')
    time_range = request.GET.get('timeRange', 'all')
    category_filter = request.GET.get('category', 'all')
    priority_filter = request.GET.get('priority', 'all')
   
    # print(f"Risk Metrics by Category - Framework: {framework_id}, Policy: {policy_id}, Time: {time_range}, Category: {category_filter}, Priority: {priority_filter}")
   
    # First, get all available categories from the categoryunit table
    from ...models import CategoryBusinessUnit
    available_categories = CategoryBusinessUnit.objects.filter(source='RiskCategory').values_list('value', flat=True)
   
    # Fetch all risk instances
    queryset = RiskInstance.objects.all()
    # print(f"Starting with all risk instances for category metrics: {queryset.count()} risks")
    
    # Apply framework filter - RiskInstance has direct ForeignKey to Framework
    if framework_id and framework_id != 'all':
        queryset = queryset.filter(FrameworkId=framework_id)
        # print(f"Applied framework filter: {framework_id}, count: {queryset.count()}")
    else:
        # When 'all' is selected, show all risks across all frameworks (no filtering)
        print(f"No framework filter applied for category metrics (All Frameworks selected), found {queryset.count()} risks")
    
    # Apply policy filter - Need to filter through ComplianceId
    if policy_id and policy_id != 'all':
        from grc.models import Policy, SubPolicy, Compliance
        try:
            policy = Policy.objects.get(PolicyId=policy_id)
            subpolicy_ids = SubPolicy.objects.filter(PolicyId=policy).values_list('SubPolicyId', flat=True)
            compliance_ids = Compliance.objects.filter(SubPolicyId__in=subpolicy_ids).values_list('ComplianceId', flat=True)
            queryset = queryset.filter(ComplianceId__in=compliance_ids)
            print(f"Applied policy filter: {policy.PolicyName}, count: {queryset.count()}")
        except Policy.DoesNotExist:
            print(f"Policy with ID {policy_id} not found")
   
    # Apply time filter if not 'all'
    if time_range != 'all':
        today = timezone.now().date()
        if time_range == '7days':
            start_date = today - timedelta(days=7)
        elif time_range == '30days':
            start_date = today - timedelta(days=30)
        elif time_range == '90days':
            start_date = today - timedelta(days=90)
        elif time_range == '1year':
            start_date = today - timedelta(days=365)
        else:
            start_date = None
           
        if start_date:
            queryset = queryset.filter(CreatedAt__gte=start_date)
   
    # Apply category filter if not 'all'
    if category_filter != 'all':
        # Handle the case conversion between frontend and backend naming
        category_map = {
            'operational': 'Operational',
            'financial': 'Financial',
            'strategic': 'Strategic',
            'compliance': 'Compliance',
            'it-security': 'IT Security'
        }
        db_category = category_map.get(category_filter, category_filter)
        queryset = queryset.filter(Category__iexact=db_category)
   
    # Apply priority filter if not 'all'
    if priority_filter != 'all':
        # Handle the case conversion between frontend and backend naming
        priority_map = {
            'critical': 'Critical',
            'high': 'High',
            'medium': 'Medium',
            'low': 'Low'
        }
        db_priority = priority_map.get(priority_filter, priority_filter)
        queryset = queryset.filter(RiskPriority__iexact=db_priority)
   
    # Group by Category and count
    from django.db.models import Count
    category_counts = queryset.values('Category').annotate(count=Count('Category')).order_by('-count')
   
    # Create a dictionary of category counts
    category_count_dict = {}
    for entry in category_counts:
        category = entry['Category'] or 'Uncategorized'
        count = entry['count']
        category_count_dict[category] = count
   
    # Prepare the response - include all available categories, even with 0 count
    categories = []
    total = 0
   
    # Add all available categories from categoryunit table
    for category in available_categories:
        count = category_count_dict.get(category, 0)
        categories.append({'category': category, 'count': count})
        total += count
   
    # Add any categories that exist in risk_instance but not in categoryunit (for backward compatibility)
    for category, count in category_count_dict.items():
        if category not in available_categories and category != 'Uncategorized':
            categories.append({'category': category, 'count': count})
            total += count
   
    # Sort by count descending
    categories.sort(key=lambda x: x['count'], reverse=True)
   
    return JsonResponse({
        'categories': categories,
        'total': total
    })
 
@api_view(['GET'])
@rbac_required(required_permission='view_all_risk')
def get_risk_categories_for_dropdown(request):
    """
    Get all risk categories from CategoryBusinessUnit for dropdown selection
    """
    try:
        from ...models import CategoryBusinessUnit
        categories = CategoryBusinessUnit.objects.filter(source='RiskCategory').order_by('value')
       
        category_data = []
        for category in categories:
            category_data.append({
                'id': category.id,
                'value': category.value
            })
       
        return Response({
            'status': 'success',
            'data': category_data
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)
 
@csrf_exempt
@api_view(['POST'])
@permission_classes([RiskCreatePermission])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
# @rbac_required(required_permission='create_risk')  # Temporarily disabled for development
@require_consent('create_risk')
def create_risk_instance(request):
    """Create a new risk instance - function-based view to avoid CSRF issues"""
    try:
        print("Received risk creation data:", request.data)
        
        # Log the create operation
        send_log(
            module="Risk",
            actionType="CREATE",
            description="Creating new risk instance",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="RiskInstance"
        )
        
        print("Original request data:", request.data)
        
        # Create a mutable copy of the data
        mutable_data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)

        # Add framework ID from session/context
        from .framework_filter_helper import get_active_framework_filter
        framework_id = get_active_framework_filter(request)
        
        if framework_id:
            # Add framework ID if one is selected
            mutable_data['FrameworkId'] = framework_id
            print(f"✅ [RISK CREATE] Adding FrameworkId to new risk instance: {framework_id}")
        else:
            # No framework selected - allow NULL/None
            mutable_data['FrameworkId'] = None
            print("ℹ️ [RISK CREATE] No framework selected - creating risk instance without framework ID")
        
        # Use the serializer to validate and create
        serializer = RiskInstanceSerializer(data=mutable_data)
        if serializer.is_valid():
            risk_instance = serializer.save()
            
            # Log successful creation
            send_log(
                module="Risk",
                actionType="CREATE_SUCCESS",
                description=f"Risk instance created successfully: {risk_instance.RiskInstanceId}",
                userId=request.user.id if request.user.is_authenticated else None,
                userName=request.user.username if request.user.is_authenticated else None,
                entityType="RiskInstance",
                entityId=risk_instance.RiskInstanceId
            )
            
            return Response(serializer.data, status=201)
        else:
            print("Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=400)
            
    except Exception as e:
        print(f"Error creating risk instance: {e}")
        import traceback
        traceback.print_exc()
        
        # Log error
        send_log(
            module="Risk",
            actionType="CREATE_ERROR",
            description=f"Error creating risk instance: {str(e)}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="RiskInstance",
            logLevel="ERROR"
        )
        
        return Response({"error": str(e)}, status=500)


@csrf_exempt
@require_consent('upload_risk')
def upload_risk_evidence_file(request):
    """
    Upload evidence files for risk mitigations.
    Supports multiple file uploads and stores them securely.
    """
    # Only allow POST requests
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Method not allowed'
        }, status=405)
    
    try:
        # Debug logging
        print(f"Content-Type: {request.content_type}")
        print(f"POST data: {request.POST}")
        print(f"FILES data: {request.FILES}")
        print(f"Request method: {request.method}")
        
        # Get user info for logging from POST data (FormData)
        user_id = request.POST.get('user_id')
        risk_instance_id = request.POST.get('risk_instance_id')
        
        if not request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No files provided'
            }, status=400)
        
        uploaded_files = []
        handler = SecureFileUploadHandler()
        
        # Process each uploaded file
        for field_name, file in request.FILES.items():
            try:
                print(f"Processing file: {file.name}, Size: {file.size}, Type: {file.content_type}")
                
                # Extract file extension
                file_name = file.name
                file_ext = Path(file_name).suffix.lower()
                
                # File size check
                if file.size > handler.MAX_FILE_SIZE:
                    return JsonResponse({
                        'success': False,
                        'error': f'File size exceeds {handler.MAX_FILE_SIZE // (1024*1024)}MB limit'
                    }, status=400)
                
                # MIME type validation
                if file.content_type not in handler.ALLOWED_MIME_TYPES:
                    return JsonResponse({
                        'success': False,
                        'error': f'File type {file.content_type} not allowed'
                    }, status=400)
                
                # Create temporary file for S3 upload
                import tempfile
                import os
                
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                        for chunk in file.chunks():
                            temp_file.write(chunk)
                        temp_file_path = temp_file.name
                    print(f"DEBUG: Temporary file created: {temp_file_path}")
                except Exception as e:
                    print(f"DEBUG: Error creating temporary file: {str(e)}")
                    return JsonResponse({
                        'success': False,
                        'error': f'Error saving file temporarily: {str(e)}'
                    }, status=500)
                
                try:
                    # Create S3 client
                    print("DEBUG: Creating S3 client...")
                    s3_client = get_s3_client()
                    
                    # Test connection first
                    print("DEBUG: Testing S3 connection...")
                    connection_test = s3_client.test_connection()
                    print(f"DEBUG: Connection test result: {connection_test}")
                    
                    if not connection_test.get('overall_success', False):
                        print("DEBUG: S3 connection test failed")
                        return JsonResponse({
                            'success': False,
                            'error': 'S3 service is currently unavailable. Please try again later.',
                            'details': connection_test
                        }, status=503)
                    
                    # Generate unique file name to avoid conflicts
                    from datetime import datetime
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    unique_file_name = f"risk_evidence_{risk_instance_id}_{timestamp}_{file_name}"
                    
                    print(f"DEBUG: Generated unique filename: {unique_file_name}")
                    
                    # Upload to S3
                    print(f"DEBUG: Starting S3 upload...")
                    upload_result = s3_client.upload(
                        file_path=temp_file_path,
                        user_id=user_id or "system",
                        custom_file_name=unique_file_name,
                        module='Risk'
                    )
                    
                    print(f"DEBUG: S3 upload result: {upload_result}")
                    
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_file_path)
                        print(f"DEBUG: Cleaned up temporary file: {temp_file_path}")
                    except Exception as cleanup_error:
                        print(f"DEBUG: Error cleaning up temp file: {cleanup_error}")
                
                if upload_result.get('success'):
                    file_info = upload_result.get('file_info', {})
                    
                    # Create file data structure similar to incident format
                    file_data = {
                        'fileName': file.name,
                        'aws-file_link': file_info.get('url', ''),
                        's3_key': file_info.get('s3_key', ''),
                        'stored_name': file_info.get('stored_name', ''),
                        'file_id': file_info.get('file_id', ''),
                        'upload_type': 's3',
                        'size': file.size,
                        'uploadedAt': file_info.get('uploaded_at', ''),
                        'category': 'risk-evidence'
                    }
                    uploaded_files.append(file_data)
                    
                    # Log successful upload
                    send_log(
                        module="Risk",
                        actionType="FILE_UPLOAD",
                        description=f"Uploaded evidence file: {file.name} for risk {risk_instance_id}",
                        userId=user_id,
                        entityType="RiskInstance",
                        entityId=risk_instance_id,
                        additionalInfo={"file_name": file.name, "file_size": file.size}
                    )
                else:
                    print(f"Upload failed for {file.name}: {upload_result.get('error', 'Unknown error')}")
                    return JsonResponse({
                        'success': False,
                        'error': f"Failed to upload {file.name}: {upload_result.get('error', 'Unknown error')}"
                    }, status=500)
                    
            except Exception as e:
                print(f"Error processing file {file.name}: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'error': f'Error processing file {file.name}: {str(e)}'
                }, status=500)
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully uploaded {len(uploaded_files)} file(s)',
            'files': uploaded_files
        })
        
    except Exception as e:
        print(f"Error in upload_risk_evidence_file: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }, status=500)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])  # Temporarily allow all for debugging
def link_evidence_to_risk(request):
    """
    Link multiple selected events as evidence to a risk instance
    """
    try:
        # Debug: Print raw request data
        print(f"DEBUG: Request method: {request.method}")
        print(f"DEBUG: Content-Type: {request.content_type}")
        print(f"DEBUG: Raw request data: {request.data}")
        print(f"DEBUG: Request POST: {request.POST}")
        
        # Get data from request.data (Django REST Framework handles JSON parsing)
        data = request.data
        print(f"DEBUG: Parsed data from request.data: {data}")
        
        risk_instance_id = data.get('risk_instance_id')
        user_id = data.get('user_id')
        linked_events = data.get('linked_events', [])
        
        print(f"DEBUG: Linking evidence to risk instance {risk_instance_id}")
        print(f"DEBUG: User ID: {user_id}")
        print(f"DEBUG: Linked events: {linked_events}")
        print(f"DEBUG: Data keys: {list(data.keys()) if data else 'No data'}")
        
        if not risk_instance_id:
            print(f"DEBUG: Risk instance ID is missing. Received data: {data}")
            return JsonResponse({
                'success': False,
                'message': 'Risk instance ID is required. Please ensure you are uploading from a valid risk workflow.',
                'debug_info': {
                    'received_data': data,
                    'risk_instance_id': risk_instance_id,
                    'user_id': user_id
                }
            }, status=400)
            
        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'User ID is required'
            }, status=400)
            
        if not linked_events or len(linked_events) == 0:
            return JsonResponse({
                'success': False,
                'message': 'At least one event must be selected'
            }, status=400)
        
        # Transform events data for storage
        evidence_data = []
        for event in linked_events:
            # Extract documents from different sources
            documents = []
            
            # 1. Check for Event evidence (S3 URLs from RiskaVaire/Event System)
            if event.get('source') in ['Riskavaire', 'RiskaVaire Module', 'Event System']:
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
            
            # Store the event with its documents
            evidence_data.append({
                'event_id': event.get('id'),
                'event_title': event.get('title', 'Unknown Event'),
                'event_source': event.get('source', 'Unknown'),
                'event_date': event.get('date', ''),
                'documents': documents
            })
        
        # Log the evidence linking activity
        send_log(
            module="Risk Evidence Linking",
            actionType="EVIDENCE_LINKED",
            description=f"Linked {len(evidence_data)} events as evidence to risk instance {risk_instance_id}",
            userId=user_id,
            ipAddress=get_client_ip(request),
            additionalInfo={
                'risk_instance_id': risk_instance_id,
                'linked_events_count': len(evidence_data),
                'events': [{'id': ev['event_id'], 'title': ev['event_title'], 'source': ev['event_source']} for ev in evidence_data]
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully linked {len(evidence_data)} events as evidence',
            'linked_events': evidence_data
        })
        
    except Exception as e:
        # Log the error with more details
        print(f"DEBUG: Exception in link_evidence_to_risk: {str(e)}")
        print(f"DEBUG: Exception type: {type(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        
        send_log(
            module="Risk Evidence Linking",
            actionType="EVIDENCE_LINKING_ERROR",
            description=f"Error linking evidence to risk instance: {str(e)}",
            userId=request.data.get('user_id') if hasattr(request, 'data') else None,
            ipAddress=get_client_ip(request),
            logLevel='ERROR',
            additionalInfo={
                'error': str(e),
                'error_type': str(type(e)),
                'traceback': traceback.format_exc(),
                'risk_instance_id': request.data.get('risk_instance_id') if hasattr(request, 'data') else None
            }
        )
        
        return JsonResponse({
            'success': False,
            'error': f'Failed to link evidence: {str(e)}',
            'error_type': str(type(e)),
            'debug_info': {
                'request_method': request.method,
                'content_type': request.content_type,
                'has_data': hasattr(request, 'data') and request.data is not None
            }
        }, status=500)


@csrf_exempt
@api_view(['GET', 'POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])
def test_link_evidence_endpoint(request):
    """
    Simple test endpoint to verify the link evidence functionality
    """
    try:
        if request.method == 'GET':
            return JsonResponse({
                'success': True,
                'message': 'Link evidence endpoint is working',
                'method': 'GET'
            })
        
        # For POST requests, just echo back the data
        data = request.data
        if not data:
            try:
                import json
                data = json.loads(request.body.decode('utf-8'))
            except:
                data = {}
        
        return JsonResponse({
            'success': True,
            'message': 'Link evidence endpoint received data',
            'received_data': data,
            'method': 'POST'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)