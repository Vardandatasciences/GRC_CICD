# Django ORM type checking suppression for this entire file
# mypy: disable-error-code="attr-defined"
# pylint: disable=no-member
# type: ignore

import logging
from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from ...rbac.decorators import (
    compliance_export_required
)
from ...rbac.permissions import (
    ComplianceExportPermission
)
from ...rbac.utils import RBACUtils
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from ...serializers import UserSerializer
from ...models import (
    User, Framework, Policy, SubPolicy, Compliance, PolicyApproval, ComplianceApproval, 
    Notification, FrameworkVersion, PolicyVersion, LastChecklistItemVerified,
    AuditVersion, AuditFinding, RiskInstance, ExportTask, GRCLog
)
from ...serializers import *
from django.utils import timezone   
import datetime
import uuid
from django.db import models
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from ...routes.Global.s3_fucntions import export_data
import json

# Configure logging
logger = logging.getLogger(__name__)

@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])  # Will be replaced with proper RBAC later
def export_compliance_management(request):
    """
    Export compliance management data to various formats
    
    Expected payload:
    {
        "export_format": "xlsx|csv|pdf|json|xml",
        "compliance_data": [...],
        "user_id": "string",
        "file_name": "string"
    }
    """
    try:
        # Log the incoming request
        logger.info(f"Compliance export request received from user: {request.user}")
        
        # Get request data
        export_format = request.data.get('export_format', 'xlsx')
        compliance_data = request.data.get('compliance_data', [])
        user_id = request.data.get('user_id', 'default_user')
        file_name = request.data.get('file_name', 'compliance_management_export')
        
        # Validate required fields
        if not compliance_data:
            return Response({
                'success': False,
                'error': 'No compliance data provided for export'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not export_format:
            return Response({
                'success': False,
                'error': 'Export format is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate export format
        supported_formats = ['xlsx', 'csv', 'pdf', 'json', 'xml', 'txt']
        if export_format not in supported_formats:
            return Response({
                'success': False,
                'error': f'Unsupported export format: {export_format}. Supported formats: {supported_formats}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Log export details
        logger.info(f"Starting compliance export: format={export_format}, records={len(compliance_data)}, user={user_id}")
        
        # Prepare export options
        export_options = {
            'file_name': f"{file_name}.{export_format}",
            'filters': {
                'export_type': 'compliance_management',
                'timestamp': datetime.datetime.now().isoformat(),
                'user_id': user_id
            },
            'columns': list(compliance_data[0].keys()) if compliance_data else []
        }
        
        # Call the export service
        export_result = export_data(
            data=compliance_data,
            file_format=export_format,
            user_id=user_id,
            options=export_options
        )
        
        if export_result['success']:
            logger.info(f"Compliance export successful: {export_result['file_url']}")
            
            # Log the export activity
            try:
                GRCLog.objects.create(
                    user_id=user_id,
                    action='COMPLIANCE_EXPORT',
                    model_name='Compliance',
                    object_id=None,
                    details=json.dumps({
                        'export_format': export_format,
                        'record_count': len(compliance_data),
                        'file_name': export_result['file_name'],
                        'export_id': export_result.get('export_id'),
                        'method': export_result['metadata'].get('method', 'unknown')
                    }),
                    timestamp=timezone.now()
                )
            except Exception as log_error:
                logger.warning(f"Failed to log export activity: {str(log_error)}")
            
            return Response({
                'success': True,
                'message': 'Compliance data exported successfully',
                'file_url': export_result['file_url'],
                'file_name': export_result['file_name'],
                'export_id': export_result.get('export_id'),
                'metadata': {
                    'record_count': len(compliance_data),
                    'export_format': export_format,
                    'file_size': export_result['metadata'].get('file_size', 0),
                    'export_duration': export_result['metadata'].get('export_duration', 0),
                    'method': export_result['metadata'].get('method', 'unknown')
                }
            }, status=status.HTTP_200_OK)
        else:
            logger.error(f"Compliance export failed: {export_result['error']}")
            return Response({
                'success': False,
                'error': export_result['error'],
                'message': 'Failed to export compliance data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Compliance export error: {str(e)}")
        return Response({
            'success': False,
            'error': str(e),
            'message': 'An unexpected error occurred during export'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])  # Will be replaced with proper RBAC later
def get_export_status(request, export_id):
    """
    Get the status of an export operation
    """
    try:
        # This would typically query the export status from the database
        # For now, return a simple response
        return Response({
            'success': True,
            'export_id': export_id,
            'status': 'completed',
            'message': 'Export status retrieved successfully'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error getting export status: {str(e)}")
        return Response({
            'success': False,
            'error': str(e),
            'message': 'Failed to get export status'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])  # Will be replaced with proper RBAC later
def list_export_history(request):
    """
    List export history for the current user
    """
    try:
        user_id = request.GET.get('user_id', 'default_user')
        
        # This would typically query the export history from the database
        # For now, return a simple response
        return Response({
            'success': True,
            'exports': [],
            'message': 'Export history retrieved successfully'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error getting export history: {str(e)}")
        return Response({
            'success': False,
            'error': str(e),
            'message': 'Failed to get export history'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
