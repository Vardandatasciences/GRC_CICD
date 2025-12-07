"""
KPI Management API
Provides endpoints for fetching and displaying KPIs from the database
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from grc.models import Kpi, Framework
from django.db.models import Q
import json


@csrf_exempt
@require_http_methods(["GET"])
def get_all_kpis(request):
    """
    Get all KPIs from the database
    Optional query parameters:
    - framework_id: Filter by framework
    - module: Filter by module (Policy, Compliance, Audit, Risk, Incident)
    """
    try:
        framework_id = request.GET.get('framework_id')
        module = request.GET.get('module')
        
        # Build query
        query = Q()
        if framework_id:
            query &= Q(FrameworkId=framework_id)
        if module:
            query &= Q(Module__iexact=module)
        
        # Fetch KPIs
        kpis = Kpi.objects.filter(query).select_related('FrameworkId')
        
        # Serialize data
        kpi_list = []
        for kpi in kpis:
            kpi_data = {
                'id': kpi.KpiId,
                'name': kpi.Name,
                'description': kpi.Description,
                'value': kpi.Value,
                'dataType': kpi.DataType,
                'displayType': kpi.DisplayType,
                'module': kpi.Module,
                'frameworkId': kpi.FrameworkId.FrameworkId if kpi.FrameworkId else None,
                'frameworkName': kpi.FrameworkName,
                'formula': kpi.Formula,
                'fromWhereToAccessData': kpi.FromWhereToAccessData,
                'auditTrail': kpi.AuditTrail,
                'createdAt': kpi.CreatedAt.isoformat() if kpi.CreatedAt else None,
                'updatedAt': kpi.UpdatedAt.isoformat() if kpi.UpdatedAt else None,
            }
            kpi_list.append(kpi_data)
        
        return JsonResponse({
            'status': 'success',
            'data': kpi_list,
            'count': len(kpi_list)
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_kpi_by_id(request, kpi_id):
    """
    Get a specific KPI by ID
    """
    try:
        kpi = Kpi.objects.select_related('FrameworkId').get(KpiId=kpi_id)
        
        kpi_data = {
            'id': kpi.KpiId,
            'name': kpi.Name,
            'description': kpi.Description,
            'value': kpi.Value,
            'dataType': kpi.DataType,
            'displayType': kpi.DisplayType,
            'module': kpi.Module,
            'frameworkId': kpi.FrameworkId.FrameworkId if kpi.FrameworkId else None,
            'frameworkName': kpi.FrameworkName,
            'formula': kpi.Formula,
            'fromWhereToAccessData': kpi.FromWhereToAccessData,
            'auditTrail': kpi.AuditTrail,
            'createdAt': kpi.CreatedAt.isoformat() if kpi.CreatedAt else None,
            'updatedAt': kpi.UpdatedAt.isoformat() if kpi.UpdatedAt else None,
        }
        
        return JsonResponse({
            'status': 'success',
            'data': kpi_data
        })
        
    except Kpi.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'KPI not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_kpis_by_module(request, module):
    """
    Get all KPIs for a specific module
    """
    try:
        kpis = Kpi.objects.filter(Module__iexact=module).select_related('FrameworkId')
        
        kpi_list = []
        for kpi in kpis:
            kpi_data = {
                'id': kpi.KpiId,
                'name': kpi.Name,
                'description': kpi.Description,
                'value': kpi.Value,
                'dataType': kpi.DataType,
                'displayType': kpi.DisplayType,
                'module': kpi.Module,
                'frameworkId': kpi.FrameworkId.FrameworkId if kpi.FrameworkId else None,
                'frameworkName': kpi.FrameworkName,
                'formula': kpi.Formula,
                'fromWhereToAccessData': kpi.FromWhereToAccessData,
                'auditTrail': kpi.AuditTrail,
                'createdAt': kpi.CreatedAt.isoformat() if kpi.CreatedAt else None,
                'updatedAt': kpi.UpdatedAt.isoformat() if kpi.UpdatedAt else None,
            }
            kpi_list.append(kpi_data)
        
        return JsonResponse({
            'status': 'success',
            'module': module,
            'data': kpi_list,
            'count': len(kpi_list)
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_frameworks_for_kpi(request):
    """
    Get all frameworks for KPI filtering
    """
    try:
        frameworks = Framework.objects.all().values('FrameworkId', 'FrameworkName')
        
        return JsonResponse({
            'status': 'success',
            'data': list(frameworks)
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_kpi_modules(request):
    """
    Get all unique modules that have KPIs
    """
    try:
        modules = Kpi.objects.values_list('Module', flat=True).distinct()
        modules = [m for m in modules if m]  # Filter out None values
        
        return JsonResponse({
            'status': 'success',
            'data': modules
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

