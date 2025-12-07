from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import datetime, timedelta
import json

from grc.models import RiskInstance, Framework, Policy, SubPolicy
from grc.rbac.permissions import RiskViewPermission, RiskAnalyticsPermission
from grc.rbac.decorators import rbac_required

# Framework filtering helper
from .framework_filter_helper import (
    apply_framework_filter_to_risk_instances,
    get_framework_filter_info
)


@api_view(['GET'])
@csrf_exempt
@permission_classes([RiskViewPermission])
@rbac_required(required_permission='view_all_risk')
def get_risk_dashboard_with_filters(request):
    """Get risk dashboard data with framework and policy filters"""
    try:
        # Get filter parameters
        framework_id = request.query_params.get('framework_id')
        policy_id = request.query_params.get('policy_id')
        time_range = request.query_params.get('timeRange', '6months')
        category = request.query_params.get('category', 'all')
        priority = request.query_params.get('priority', 'all')
        
        print(f"Risk Dashboard Filters - Framework: {framework_id}, Policy: {policy_id}, Time: {time_range}, Category: {category}, Priority: {priority}")
        
        # Start with all risk instances
        queryset = RiskInstance.objects.all()
        print(f"Starting with all risk instances: {queryset.count()} risks")
        
        # Apply framework filter - RiskInstance has direct ForeignKey to Framework
        if framework_id and framework_id != 'all':
            # Use the framework_id from frontend filter
            queryset = queryset.filter(FrameworkId=framework_id)
            print(f"Applied frontend framework filter: {framework_id}, found {queryset.count()} risks")
        else:
            # When 'all' is selected, show all risks across all frameworks (no filtering)
            print(f"No framework filter applied (All Frameworks selected), found {queryset.count()} risks")
        
        # Apply policy filter - Need to filter through ComplianceId
        if policy_id and policy_id != 'all':
            try:
                policy = Policy.objects.get(PolicyId=policy_id)
                # Get all subpolicies in this policy
                subpolicy_ids = SubPolicy.objects.filter(PolicyId=policy).values_list('SubPolicyId', flat=True)
                # Get all compliance IDs for these subpolicies
                from grc.models import Compliance
                compliance_ids = Compliance.objects.filter(SubPolicyId__in=subpolicy_ids).values_list('ComplianceId', flat=True)
                # Filter risks by compliance
                queryset = queryset.filter(ComplianceId__in=compliance_ids)
                print(f"Applied policy filter: {policy.PolicyName}, found {queryset.count()} risks")
            except Policy.DoesNotExist:
                print(f"Policy with ID {policy_id} not found")
                return Response({'error': 'Policy not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Apply time range filter
        if time_range != 'all':
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
                start_date = end_date - timedelta(days=180)  # Default to 6 months
            
            queryset = queryset.filter(CreatedAt__gte=start_date, CreatedAt__lte=end_date)
            print(f"Applied time filter: {time_range}, found {queryset.count()} risks")
        
        # Apply category filter
        if category and category != 'all':
            queryset = queryset.filter(Category=category)
            print(f"Applied category filter: {category}, found {queryset.count()} risks")
        
        # Apply priority filter
        if priority and priority != 'all':
            queryset = queryset.filter(RiskPriority=priority)
            print(f"Applied priority filter: {priority}, found {queryset.count()} risks")
        
        # Calculate metrics
        total_risks = queryset.count()
        accepted_risks = queryset.filter(RiskStatus='Approved').count()
        rejected_risks = queryset.filter(RiskStatus='Rejected').count()
        mitigated_risks = queryset.filter(MitigationStatus=RiskInstance.MITIGATION_COMPLETED).count()
        in_progress_risks = queryset.filter(MitigationStatus=RiskInstance.MITIGATION_IN_PROGRESS).count()
        
        print(f"Risk metrics calculated - Total: {total_risks}, Accepted: {accepted_risks}, Rejected: {rejected_risks}, Mitigated: {mitigated_risks}, In Progress: {in_progress_risks}")
        
        # Calculate averages
        avg_impact = queryset.aggregate(avg_impact=Avg('RiskImpact'))['avg_impact'] or 0
        avg_likelihood = queryset.aggregate(avg_likelihood=Avg('RiskLikelihood'))['avg_likelihood'] or 0
        
        # Get category distribution
        category_distribution = queryset.values('Category').annotate(
            count=Count('RiskInstanceId')
        ).order_by('-count')
        
        print(f"Category distribution calculated: {list(category_distribution)}")
        
        # Get status distribution
        status_distribution = queryset.values('RiskStatus').annotate(
            count=Count('RiskInstanceId')
        ).order_by('-count')
        
        # Get priority distribution
        priority_distribution = queryset.values('RiskPriority').annotate(
            count=Count('RiskInstanceId')
        ).order_by('-count')
        
        # Prepare response data
        dashboard_data = {
            'success': True,
            'data': {
                'summary': {
                    'total_count': total_risks,
                    'accepted_count': accepted_risks,
                    'rejected_count': rejected_risks,
                    'mitigated_count': mitigated_risks,
                    'in_progress_count': in_progress_risks,
                    'avg_impact': round(avg_impact, 2),
                    'avg_likelihood': round(avg_likelihood, 2)
                },
                'category_distribution': list(category_distribution),
                'status_distribution': list(status_distribution),
                'priority_distribution': list(priority_distribution),
                'filters_applied': {
                    'framework_id': framework_id,
                    'policy_id': policy_id,
                    'time_range': time_range,
                    'category': category,
                    'priority': priority
                }
            }
        }
        
        print(f"Risk dashboard data prepared: {total_risks} total risks")
        return Response(dashboard_data)
        
    except Exception as e:
        print(f"Error in get_risk_dashboard_with_filters: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to fetch risk dashboard data'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@csrf_exempt
@permission_classes([RiskAnalyticsPermission])
@rbac_required(required_permission='risk_performance_analytics')
def get_risk_analytics_with_filters(request):
    """Get risk analytics data with framework and policy filters"""
    try:
        data = request.data
        x_axis = data.get('xAxis')
        y_axis = data.get('yAxis')
        framework_id = data.get('frameworkId')
        policy_id = data.get('policyId')
        time_range = data.get('timeRange', '6months')
        category = data.get('category', 'all')
        priority = data.get('priority', 'all')
        
        print(f"Risk Analytics Filters - X: {x_axis}, Y: {y_axis}, Framework: {framework_id}, Policy: {policy_id}")
        
        # Start with all risk instances
        queryset = RiskInstance.objects.all()
        print(f"Starting with all risk instances for analytics: {queryset.count()} risks")
        
        # Apply framework filter - RiskInstance has direct ForeignKey to Framework
        if framework_id and framework_id != 'all':
            # Use the framework_id from frontend filter
            queryset = queryset.filter(FrameworkId=framework_id)
            print(f"Applied frontend framework filter for analytics: {framework_id}, found {queryset.count()} risks")
        else:
            # When 'all' is selected, show all risks across all frameworks (no filtering)
            print(f"No framework filter applied for analytics (All Frameworks selected), found {queryset.count()} risks")
        
        # Apply policy filter - Need to filter through ComplianceId
        if policy_id and policy_id != 'all':
            try:
                policy = Policy.objects.get(PolicyId=policy_id)
                subpolicy_ids = SubPolicy.objects.filter(PolicyId=policy).values_list('SubPolicyId', flat=True)
                from grc.models import Compliance
                compliance_ids = Compliance.objects.filter(SubPolicyId__in=subpolicy_ids).values_list('ComplianceId', flat=True)
                queryset = queryset.filter(ComplianceId__in=compliance_ids)
            except Policy.DoesNotExist:
                return Response({'error': 'Policy not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Apply time range filter
        if time_range != 'all':
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
        
        # Apply category filter
        if category and category != 'all':
            queryset = queryset.filter(Category=category)
        
        # Apply priority filter
        if priority and priority != 'all':
            queryset = queryset.filter(RiskPriority=priority)
        
        # Generate chart data based on x_axis and y_axis
        chart_data = generate_risk_chart_data(queryset, x_axis, y_axis)
        
        response_data = {
            'success': True,
            'chartData': chart_data,
            'filters_applied': {
                'framework_id': framework_id,
                'policy_id': policy_id,
                'time_range': time_range,
                'category': category,
                'priority': priority
            }
        }
        
        print(f"Risk analytics data prepared for {x_axis} vs {y_axis}")
        return Response(response_data)
        
    except Exception as e:
        print(f"Error in get_risk_analytics_with_filters: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to fetch risk analytics data'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def generate_risk_chart_data(queryset, x_axis, y_axis):
    """Generate chart data based on x_axis and y_axis parameters"""
    
    if x_axis == 'category':
        # Group by risk category
        data = queryset.values('Category').annotate(
            count=Count('RiskInstanceId'),
            avg_impact=Avg('RiskImpact'),
            avg_likelihood=Avg('RiskLikelihood'),
            avg_exposure=Avg('RiskExposureRating')
        ).order_by('-count')
        
        labels = [item['Category'] for item in data]
        
        if y_axis == 'count':
            values = [item['count'] for item in data]
        elif y_axis == 'impact':
            values = [round(item['avg_impact'], 2) for item in data]
        elif y_axis == 'likelihood':
            values = [round(item['avg_likelihood'], 2) for item in data]
        elif y_axis == 'exposure':
            values = [round(item['avg_exposure'], 2) for item in data]
        else:
            values = [item['count'] for item in data]
    
    elif x_axis == 'status':
        # Group by risk status
        data = queryset.values('RiskStatus').annotate(
            count=Count('RiskInstanceId'),
            avg_impact=Avg('RiskImpact'),
            avg_likelihood=Avg('RiskLikelihood')
        ).order_by('-count')
        
        labels = [item['RiskStatus'] for item in data]
        
        if y_axis == 'count':
            values = [item['count'] for item in data]
        elif y_axis == 'impact':
            values = [round(item['avg_impact'], 2) for item in data]
        elif y_axis == 'likelihood':
            values = [round(item['avg_likelihood'], 2) for item in data]
        else:
            values = [item['count'] for item in data]
    
    elif x_axis == 'priority':
        # Group by risk priority
        data = queryset.values('RiskPriority').annotate(
            count=Count('RiskInstanceId'),
            avg_impact=Avg('RiskImpact'),
            avg_likelihood=Avg('RiskLikelihood')
        ).order_by('-count')
        
        labels = [item['RiskPriority'] for item in data]
        
        if y_axis == 'count':
            values = [item['count'] for item in data]
        elif y_axis == 'impact':
            values = [round(item['avg_impact'], 2) for item in data]
        elif y_axis == 'likelihood':
            values = [round(item['avg_likelihood'], 2) for item in data]
        else:
            values = [item['count'] for item in data]
    
    elif x_axis == 'time':
        # Group by month using Django's built-in date functions
        from django.db.models.functions import TruncMonth
        data = queryset.annotate(
            month=TruncMonth('CreatedAt')
        ).values('month').annotate(
            count=Count('RiskInstanceId'),
            avg_impact=Avg('RiskImpact'),
            avg_likelihood=Avg('RiskLikelihood')
        ).order_by('month')
        
        labels = [item['month'] for item in data]
        
        if y_axis == 'count':
            values = [item['count'] for item in data]
        elif y_axis == 'impact':
            values = [round(item['avg_impact'], 2) for item in data]
        elif y_axis == 'likelihood':
            values = [round(item['avg_likelihood'], 2) for item in data]
        else:
            values = [item['count'] for item in data]
    
    else:
        # Default: category vs count
        data = queryset.values('Category').annotate(
            count=Count('RiskInstanceId')
        ).order_by('-count')
        
        labels = [item['Category'] for item in data]
        values = [item['count'] for item in data]
    
    return {
        'labels': labels,
        'datasets': [{
            'label': f'{y_axis.title()} by {x_axis.title()}',
            'data': values,
            'backgroundColor': generate_chart_colors(len(labels)),
            'borderColor': generate_chart_colors(len(labels)),
            'borderWidth': 1
        }]
    }


def generate_chart_colors(count):
    """Generate consistent colors for charts"""
    colors = [
        '#4ade80', '#f87171', '#fbbf24', '#60a5fa', '#818cf8',
        '#f472b6', '#a78bfa', '#34d399', '#fbbf24', '#fb7185',
        '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444'
    ]
    
    result = []
    for i in range(count):
        result.append(colors[i % len(colors)])
    
    return result


@api_view(['GET'])
@csrf_exempt
@permission_classes([AllowAny])
def get_risk_frameworks_for_filter(request):
    """Get frameworks for risk dashboard filter dropdown with risk counts"""
    try:
        from django.db import connection
        
        # Get all active frameworks with risk counts using raw SQL
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    f.FrameworkId,
                    f.FrameworkName,
                    f.FrameworkDescription,
                    COUNT(r.RiskInstanceId) as risk_count
                FROM frameworks f
                LEFT JOIN risk_instance r ON f.FrameworkId = r.FrameworkId
                WHERE f.ActiveInactive = 'Active'
                GROUP BY f.FrameworkId, f.FrameworkName, f.FrameworkDescription
                ORDER BY f.FrameworkName
            """)
            
            frameworks = []
            for row in cursor.fetchall():
                frameworks.append({
                    'FrameworkId': row[0],
                    'FrameworkName': row[1],
                    'FrameworkDescription': row[2] or '',
                    'risk_count': row[3] or 0
                })
            
            print(f"Found {len(frameworks)} frameworks")
            for fw in frameworks:
                print(f"  {fw['FrameworkName']}: {fw['risk_count']} risks")
        
        return Response({
            'success': True,
            'data': frameworks
        })
        
    except Exception as e:
        print(f"Error fetching risk frameworks: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': 'Failed to fetch frameworks'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@csrf_exempt
@permission_classes([AllowAny])
def get_risk_policies_for_filter(request):
    """Get policies for risk dashboard filter dropdown"""
    try:
        framework_id = request.query_params.get('framework_id')
        
        if framework_id and framework_id != 'all':
            # Get policies for specific framework
            policies = Policy.objects.filter(
                FrameworkId=framework_id,
                ActiveInactive='Active'
            ).values(
                'PolicyId', 'PolicyName', 'PolicyDescription'
            ).order_by('PolicyName')
        else:
            # Get all active policies
            policies = Policy.objects.filter(
                ActiveInactive='Active'
            ).values(
                'PolicyId', 'PolicyName', 'PolicyDescription'
            ).order_by('PolicyName')
        
        return Response({
            'success': True,
            'data': list(policies)
        })
        
    except Exception as e:
        print(f"Error fetching risk policies: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to fetch policies'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)