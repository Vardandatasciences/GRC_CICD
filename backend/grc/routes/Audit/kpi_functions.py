from django.db.models import Count, Case, When, F, Value, FloatField, Avg, Func
from django.db.models.functions import ExtractMonth, TruncMonth
from ...models import LastChecklistItemVerified, Audit, Users, Framework, Policy, SubPolicy, Compliance, AuditFinding
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models.expressions import RawSQL
from ...routes.Global.logging_service import send_log
from django.http import JsonResponse
from django.db import connection
from dateutil.relativedelta import relativedelta
from django.db.models import F, Func, IntegerField, Value, CharField
from django.db.models.functions import Coalesce
from...rbac.decorators import audit_analytics_required
from .framework_filter_helper import get_active_framework_filter, apply_framework_filter_to_audits, get_framework_sql_filter

logger = logging.getLogger(__name__)

# Custom function to calculate date difference in days
class DateDiffInDays(Func):
    function = 'DATEDIFF'
    template = "%(function)s(%(expressions)s)"
    
    def __init__(self, end_date, start_date, **extras):
        super().__init__(end_date, start_date, **extras)

@api_view(['GET'])
@permission_classes([AllowAny])
@audit_analytics_required
def get_audit_completion_metrics(request):
    try:
        # Get time period from query params (default to current month)
        period = request.GET.get('period', 'month')
        year = request.GET.get('year', datetime.now().year)
        
        # Calculate date range
        today = timezone.now()
        if period == 'day':
            start_date = today - timedelta(days=1)
            end_date = today
        elif period == 'week':
            start_date = today - timedelta(weeks=1)
            end_date = today
        elif period == 'month':
            # Current month
            start_date = datetime(today.year, today.month, 1)
            if today.month == 12:
                end_date = datetime(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(today.year, today.month + 1, 1) - timedelta(days=1)
        else:  # year
            start_date = datetime(int(year), 1, 1)
            end_date = datetime(int(year), 12, 31)

        # Apply framework filter
        base_queryset = Audit.objects.all()
        base_queryset = apply_framework_filter_to_audits(base_queryset, request)

        # Get audit metrics
        audits = base_queryset.filter(AssignedDate__gte=start_date, AssignedDate__lte=end_date)
        
        total_audits = audits.count()
        completed_audits = audits.filter(Status='Completed').count()
        completion_percentage = (completed_audits / total_audits * 100) if total_audits > 0 else 0

        # Get monthly breakdown for the entire year
        year_start = datetime(int(year), 1, 1)
        year_end = datetime(int(year), 12, 31)
        
        # Get framework SQL filter
        where_clause, params = get_framework_sql_filter(request, 'audit')
        
        monthly_data_query = f"""
            SELECT 
                DATE_FORMAT(AssignedDate, '%%Y-%%m') AS month,
                COUNT(*) AS planned,
                SUM(CASE WHEN Status = 'Completed' THEN 1 ELSE 0 END) AS completed
            FROM 
                audit
            WHERE 
                AssignedDate BETWEEN %(year_start)s AND %(year_end)s
                {where_clause}
            GROUP BY 
                month
            ORDER BY 
                month
        """
        
        query_params = {'year_start': year_start, 'year_end': year_end}
        query_params.update(params)
        
        with connection.cursor() as cursor:
            cursor.execute(monthly_data_query, query_params)
            monthly_data = []
            
            for row in cursor.fetchall():
                month_str, planned, completed = row
                if month_str:
                    year, month = map(int, month_str.split('-'))
                    month_date = datetime(year, month, 1)
                    month_name = month_date.strftime('%b')  # Short month name
                    
                    monthly_data.append({
                        'month': month_name,
                        'month_num': month,
                        'year': year,
                        'planned': planned,
                        'completed': completed,
                        'completion_percentage': round((completed / planned * 100), 2) if planned > 0 else 0
                    })
        
        # Ensure all months are represented, even if no data
        all_months = []
        for month in range(1, 13):
            month_date = datetime(int(year), month, 1)
            month_name = month_date.strftime('%b')
            
            # Check if this month exists in the data
            month_exists = False
            for item in monthly_data:
                if item['month_num'] == month and item['year'] == int(year):
                    month_exists = True
                    all_months.append(item)
                    break
            
            if not month_exists:
                all_months.append({
                    'month': month_name,
                    'month_num': month,
                    'year': int(year),
                    'planned': 0,
                    'completed': 0,
                    'completion_percentage': 0
                })
        
        # Sort by month number
        all_months.sort(key=lambda x: x['month_num'])
        
        # Get highest planned month for scaling the chart
        max_planned = max([m['planned'] for m in all_months]) if all_months else 0
        max_completed = max([m['completed'] for m in all_months]) if all_months else 0
        chart_max = max(max_planned, max_completed, 5)  # Ensure minimum scale of 5

        response = Response({
            'success': True,
            'data': {
                'title': 'Audit Completion',
                'metrics': {
                    'total_audits': total_audits,
                    'completed_audits': completed_audits,
                    'completion_percentage': round(completion_percentage, 2)
                },
                'monthly_breakdown': all_months,
                'chart_max': chart_max,
                'period': period,
                'year': year
            }
        })
        
        # Add CORS headers
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        send_log(module="KPI", actionType="GET_AUDIT_COMPLETION_METRICS", description="Fetched audit completion metrics", userId=request.session.get('user_id'))
        
        return response

    except Exception as e:
        logger.error(f"Error in get_audit_completion_metrics: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])  # Temporarily allow any access for testing
@audit_analytics_required
def get_non_compliance_count(request):
    try:
        # Group and count by Complied values ('0' and '1')
        compliance_stats = (
            LastChecklistItemVerified.objects
            .filter(Complied__in=['0', '1'])
            .values('Complied')
            .annotate(count=Count('Complied'))
        )

        count_0 = 0  # Non-compliant
        count_1 = 0  # Compliant
        
        for entry in compliance_stats:
            if entry['Complied'] == '0':
                count_0 = entry['count']
            elif entry['Complied'] == '1':
                count_1 = entry['count']

        total = count_0 + count_1
        print(f"DEBUG: Found counts - Non-compliant: {count_0}, Compliant: {count_1}, Total: {total}")
        logger.info(f"Non-compliance counts - Non-compliant: {count_0}, Compliant: {count_1}, Total: {total}")

        response = Response({
            'success': True,
            'data': {
                'title': 'Non-Compliances',
                'value': total,
                'description': f'{count_0} non-compliances and {count_1} compliances found',
                'color': 'error' if count_0 > 0 else 'success',
                'compliance_breakdown': {
                    'complied_0': count_0,
                    'complied_1': count_1
                }
            }
        })
        
        # Add CORS headers
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        send_log(module="KPI", actionType="GET_NON_COMPLIANCE_COUNT", description="Fetched non-compliance count", userId=request.session.get('user_id'))
        
        return response
    
    except Exception as e:
        logger.error(f"Error in get_non_compliance_count: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
@audit_analytics_required
def get_audit_cycle_time(request):
    try:
        # Get framework filter from session (priority) or query params (fallback)
        framework_id = get_active_framework_filter(request)
        if not framework_id:
            framework_id = request.GET.get('framework_id')
        
        # Use all-time data by default for framework filtering
        # Calculate date range for the past year as default
        today = timezone.now()
        start_date = datetime(today.year - 1, today.month, 1)
        end_date = today
        
        # Build the query condition
        where_conditions = [
            "CompletionDate IS NOT NULL",
            "Status = 'Completed'"
        ]
        params = [start_date, end_date]
        
        # Add framework filter if provided
        if framework_id:
            where_conditions.append("FrameworkId = %s")
            params.append(framework_id)
        
        # Get frameworks list for dropdown
        frameworks_query = """
            SELECT DISTINCT 
                f.FrameworkId, 
                f.FrameworkName
            FROM 
                frameworks f
            JOIN
                audit a ON f.FrameworkId = a.FrameworkId
            WHERE
                a.CompletionDate IS NOT NULL
            ORDER BY
                f.FrameworkName
        """
        
        # Use raw SQL to calculate the date difference by month
        monthly_query = f"""
            SELECT 
                DATE_FORMAT(AssignedDate, '%%Y-%%m') AS month,
                AVG(DATEDIFF(CompletionDate, AssignedDate)) AS avg_cycle_days
            FROM 
                audit
            WHERE 
                AssignedDate BETWEEN %s AND %s
                AND {" AND ".join(where_conditions)}
            GROUP BY 
                month
            ORDER BY 
                month
        """
        
        with connection.cursor() as cursor:
            cursor.execute(frameworks_query)
            frameworks = []
            for row in cursor.fetchall():
                framework_id, framework_name = row
                frameworks.append({
                    'id': framework_id,
                    'name': framework_name or f'Framework {framework_id}'
                })
        
        # Get monthly data
        with connection.cursor() as cursor:
            cursor.execute(monthly_query, params)
            monthly_data = []
            
            for row in cursor.fetchall():
                month_str, avg_days = row
                # Parse YYYY-MM to a date object for better formatting
                year, month = map(int, month_str.split('-'))
                month_date = datetime(year, month, 1)
                
                monthly_data.append({
                    'month': month_date.strftime('%b %Y'),  # Short month name and year
                    'avg_cycle_days': round(float(avg_days), 1) if avg_days else 0
                })
        
        # Calculate overall average with the same conditions
        overall_avg_query = f"""
            SELECT 
                AVG(DATEDIFF(CompletionDate, AssignedDate)) AS overall_avg
            FROM 
                audit
            WHERE 
                AssignedDate BETWEEN %s AND %s
                AND {" AND ".join(where_conditions)}
        """
        
        # Calculate distribution data
        distribution_query = f"""
            SELECT 
                CASE
                    WHEN DATEDIFF(CompletionDate, AssignedDate) <= 5 THEN '0-5 days'
                    WHEN DATEDIFF(CompletionDate, AssignedDate) <= 10 THEN '6-10 days'
                    WHEN DATEDIFF(CompletionDate, AssignedDate) <= 15 THEN '11-15 days'
                    WHEN DATEDIFF(CompletionDate, AssignedDate) <= 20 THEN '16-20 days'
                    ELSE '21+ days'
                END AS cycle_range,
                COUNT(*) AS count
            FROM 
                audit
            WHERE 
                AssignedDate BETWEEN %s AND %s
                AND {" AND ".join(where_conditions)}
            GROUP BY 
                cycle_range
            ORDER BY 
                FIELD(cycle_range, '0-5 days', '6-10 days', '11-15 days', '16-20 days', '21+ days')
        """
        
        # Calculate additional performance metrics
        performance_query = f"""
            SELECT 
                AVG(DATEDIFF(CompletionDate, AssignedDate)) AS average_cycle_time,
                MIN(DATEDIFF(CompletionDate, AssignedDate)) AS fastest_cycle_time,
                MAX(DATEDIFF(CompletionDate, AssignedDate)) AS slowest_cycle_time,
                COUNT(*) AS total_audits
            FROM 
                audit
            WHERE 
                AssignedDate BETWEEN %s AND %s
                AND {" AND ".join(where_conditions)}
        """
        
        with connection.cursor() as cursor:
            # Get overall average
            cursor.execute(overall_avg_query, params)
            result = cursor.fetchone()
            overall_avg = round(float(result[0]), 1) if result and result[0] else 0
            
            # Get distribution data
            cursor.execute(distribution_query, params)
            distribution_data = []
            for row in cursor.fetchall():
                cycle_range, count = row
                distribution_data.append({
                    'range': cycle_range,
                    'count': count
                })
            
            # Get performance metrics
            cursor.execute(performance_query, params)
            perf_result = cursor.fetchone()
            performance_metrics = {
                'average_cycle_time': round(float(perf_result[0]), 1) if perf_result and perf_result[0] else 0,
                'fastest_cycle_time': round(float(perf_result[1]), 1) if perf_result and perf_result[1] else 0,
                'slowest_cycle_time': round(float(perf_result[2]), 1) if perf_result and perf_result[2] else 0,
                'total_audits': perf_result[3] if perf_result and perf_result[3] else 0
            }
        
        # Target days (can be made configurable later)
        target_days = 30
        
        response = Response({
            'success': True,
            'data': {
                'title': 'Audit Cycle Time',
                'metrics': {
                    'overall_avg_days': overall_avg,
                    'target_days': target_days,
                    'efficiency': 'Good' if overall_avg <= target_days else 'Needs Improvement',
                    'average_cycle_time': performance_metrics['average_cycle_time'],
                    'fastest_cycle_time': performance_metrics['fastest_cycle_time'],
                    'slowest_cycle_time': performance_metrics['slowest_cycle_time'],
                    'total_audits': performance_metrics['total_audits']
                },
                'monthly_breakdown': monthly_data,
                'distribution': distribution_data,
                'frameworks': frameworks,
                'selected_framework': framework_id
            }
        })
        
        # Add CORS headers
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        send_log(module="KPI", actionType="GET_AUDIT_CYCLE_TIME", description="Fetched audit cycle time metrics", userId=request.session.get('user_id'))
        
        return response
        
    except Exception as e:
        logger.error(f"Error in get_audit_cycle_time: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
@audit_analytics_required
def get_finding_rate(request):
    try:
        # Get time period from query params (default to current year)
        period = request.GET.get('period', 'year')
        year = request.GET.get('year', datetime.now().year)
        
        # Calculate date range
        today = timezone.now()
        if period == 'month':
            start_date = datetime(today.year, today.month, 1)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        elif period == 'quarter':
            current_quarter = (today.month - 1) // 3 + 1
            start_date = datetime(today.year, (current_quarter - 1) * 3 + 1, 1)
            if current_quarter == 4:
                end_date = datetime(today.year, 12, 31)
            else:
                end_date = datetime(today.year, current_quarter * 3 + 1, 1) - timedelta(days=1)
        else:  # year
            start_date = datetime(int(year), 1, 1)
            end_date = datetime(int(year), 12, 31)
        
        # Get framework SQL filter
        where_clause, params = get_framework_sql_filter(request, 'a')
        
        # Calculate the average non-compliant findings per audit
        # Join audit_findings to compliance on ComplianceId
        # Filter findings where Check = '0' (non-compliant)
        # Count non-compliant findings per audit
        # Average counts across all audits
        raw_query = f"""
            SELECT 
                AVG(non_compliant_count) AS avg_findings_per_audit
            FROM (
                SELECT 
                    af.AuditId, 
                    COUNT(*) AS non_compliant_count
                FROM 
                    audit_findings af
                JOIN 
                    audit a ON af.AuditId = a.AuditId
                WHERE 
                    af.Check = '0'
                    AND af.AssignedDate BETWEEN %(start_date)s AND %(end_date)s
                    {where_clause}
                GROUP BY 
                    af.AuditId
            ) AS sub;
        """
        
        # Get audits with the highest number of findings for the bar chart
        top_audits_query = f"""
            SELECT 
                a.AuditId, 
                COUNT(*) AS finding_count,
                f.FrameworkName,
                f.FrameworkId,
                p.PolicyName,
                p.PolicyId,
                sp.SubPolicyName,
                sp.SubPolicyId
            FROM 
                audit_findings af
            JOIN 
                audit a ON af.AuditId = a.AuditId
            LEFT JOIN 
                frameworks f ON a.FrameworkId = f.FrameworkId
            LEFT JOIN 
                policies p ON a.PolicyId = p.PolicyId
            LEFT JOIN
                subpolicies sp ON a.SubPolicyId = sp.SubPolicyId
            WHERE 
                af.`Check` = '0'
                AND af.AssignedDate BETWEEN %(start_date)s AND %(end_date)s
                {where_clause}
            GROUP BY 
                af.AuditId, f.FrameworkName, p.PolicyName, sp.SubPolicyName
            ORDER BY 
                finding_count DESC
            LIMIT 10;
        """
        
        query_params = {'start_date': start_date, 'end_date': end_date}
        query_params.update(params)
        
        with connection.cursor() as cursor:
            cursor.execute(raw_query, query_params)
            result = cursor.fetchone()
            avg_findings = round(float(result[0]), 2) if result[0] else 0
            
            # Get top audits with highest findings
            cursor.execute(top_audits_query, query_params)
            top_audits = []
            
            for row in cursor.fetchall():
                audit_id, finding_count, framework_name, framework_id, policy_name, policy_id, subpolicy_name, subpolicy_id = row
                top_audits.append({
                    'audit_id': audit_id,
                    'finding_count': finding_count,
                    'framework': framework_name or 'Unknown',
                    'framework_id': framework_id,
                    'policy': policy_name or 'Unknown',
                    'policy_id': policy_id,
                    'subpolicy': subpolicy_name or 'Unknown',
                    'subpolicy_id': subpolicy_id,
                    'label': f"Audit #{audit_id}"
                })
        
        # Get threshold for ratings
        low_threshold = 2
        high_threshold = 5
        
        response = Response({
            'success': True,
            'data': {
                'title': 'Finding Rate',
                'metrics': {
                    'avg_findings_per_audit': avg_findings,
                    'low_threshold': low_threshold,
                    'high_threshold': high_threshold,
                    'rating': 'Good' if avg_findings <= low_threshold else 
                             'Fair' if avg_findings <= high_threshold else 'Poor'
                },
                'top_audits': top_audits,
                'period': period,
                'year': year
            }
        })
        
        # Add CORS headers
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        send_log(module="KPI", actionType="GET_FINDING_RATE", description="Fetched finding rate metrics", userId=request.session.get('user_id'))
        
        return response
        
    except Exception as e:
        logger.error(f"Error in get_finding_rate: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
@audit_analytics_required
def get_time_to_close_findings(request):
    try:
        # Get time period from query params (default to current year)
        period = request.GET.get('period', 'year')
        year = request.GET.get('year', datetime.now().year)
        
        # Calculate date range
        today = timezone.now()
        if period == 'month':
            start_date = datetime(today.year, today.month, 1)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        elif period == 'quarter':
            current_quarter = (today.month - 1) // 3 + 1
            start_date = datetime(today.year, (current_quarter - 1) * 3 + 1, 1)
            if current_quarter == 4:
                end_date = datetime(today.year, 12, 31)
            else:
                end_date = datetime(today.year, current_quarter * 3 + 1, 1) - timedelta(days=1)
        else:  # year
            start_date = datetime(int(year), 1, 1)
            end_date = datetime(int(year), 12, 31)
        
        # Calculate average close time
        # For findings where Check = '2' (completed/closed), calculate days between ReviewDate and AssignedDate
        avg_close_time_query = """
            SELECT 
                AVG(DATEDIFF(ReviewDate, AssignedDate)) AS avg_close_days
            FROM 
                audit_findings
            WHERE 
                `Check` = '2'  -- closed/completed
                AND ReviewDate IS NOT NULL
                AND ReviewDate BETWEEN %s AND %s;
        """
        
        # Get monthly trend
        monthly_trend_query = """
            SELECT 
                DATE_FORMAT(ReviewDate, '%%Y-%%m') AS month,
                AVG(DATEDIFF(ReviewDate, AssignedDate)) AS avg_close_days
            FROM 
                audit_findings
            WHERE 
                `Check` = '2'  -- closed/completed
                AND ReviewDate IS NOT NULL
                AND ReviewDate BETWEEN %s AND %s
            GROUP BY 
                month
            ORDER BY 
                month;
        """
        
        # Get top 5 oldest open findings
        oldest_open_findings_query = """
            SELECT 
                af.AuditFindingsId, 
                af.AuditId,
                af.ComplianceId,
                af.AssignedDate,
                DATEDIFF(NOW(), af.AssignedDate) AS days_open,
                a.Status AS audit_status,
                f.FrameworkName AS framework,
                p.PolicyName AS policy
            FROM 
                audit_findings af
            JOIN
                audit a ON af.AuditId = a.AuditId
            LEFT JOIN
                frameworks f ON a.FrameworkId = f.FrameworkId
            LEFT JOIN
                policies p ON a.PolicyId = p.PolicyId
            WHERE 
                af.`Check` != '2'  -- not closed/completed
            ORDER BY 
                days_open DESC
            LIMIT 5;
        """
        
        with connection.cursor() as cursor:
            # Get average close time
            cursor.execute(avg_close_time_query, [start_date, end_date])
            result = cursor.fetchone()
            avg_close_days = round(float(result[0]), 1) if result[0] else 0
            
            # Get monthly trend
            cursor.execute(monthly_trend_query, [start_date, end_date])
            monthly_trend = []
            
            for row in cursor.fetchall():
                month_str, avg_days = row
                year, month = map(int, month_str.split('-'))
                month_date = datetime(year, month, 1)
                
                monthly_trend.append({
                    'month': month_date.strftime('%b %Y'),
                    'avg_close_days': round(float(avg_days), 1) if avg_days else 0
                })
            
            # Get top 5 oldest open findings
            cursor.execute(oldest_open_findings_query)
            oldest_findings = []
            
            for row in cursor.fetchall():
                finding_id, audit_id, compliance_id, assigned_date, days_open, audit_status, framework, policy = row
                
                if assigned_date:
                    assigned_date_str = assigned_date.strftime('%Y-%m-%d')
                else:
                    assigned_date_str = 'N/A'
                
                oldest_findings.append({
                    'finding_id': finding_id,
                    'audit_id': audit_id,
                    'compliance_id': compliance_id,
                    'assigned_date': assigned_date_str,
                    'days_open': days_open if days_open else 0,
                    'audit_status': audit_status or 'Unknown',
                    'framework': framework or 'Unknown',
                    'policy': policy or 'Unknown'
                })
        
        # Target close days (can be made configurable later)
        target_days = 14
        
        # Get efficiency rating
        if avg_close_days <= target_days:
            efficiency = 'Good'
        elif avg_close_days <= target_days * 2:
            efficiency = 'Fair'
        else:
            efficiency = 'Poor'
        
        response = Response({
            'success': True,
            'data': {
                'title': 'Time to Close Findings',
                'metrics': {
                    'avg_close_days': avg_close_days,
                    'target_days': target_days,
                    'efficiency': efficiency,
                    'oldest_open_finding': oldest_findings[0]['days_open'] if oldest_findings else 0
                },
                'monthly_trend': monthly_trend,
                'oldest_findings': oldest_findings,
                'period': period,
                'year': year
            }
        })
        
        # Add CORS headers
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        send_log(module="KPI", actionType="GET_TIME_TO_CLOSE_FINDINGS", description="Fetched time to close findings metrics", userId=request.session.get('user_id'))
        
        return response
        
    except Exception as e:
        logger.error(f"Error in get_time_to_close_findings: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
@audit_analytics_required
def get_non_compliance_issues(request):
    try:
        # Get time period from query params (default to current year)
        period = request.GET.get('period', 'year')
        year = request.GET.get('year', datetime.now().year)
        severity = request.GET.get('severity', 'all')  # all, high, medium, low
        
        # Calculate date range
        today = timezone.now()
        if period == 'month':
            start_date = datetime(today.year, today.month, 1)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        elif period == 'quarter':
            current_quarter = (today.month - 1) // 3 + 1
            start_date = datetime(today.year, (current_quarter - 1) * 3 + 1, 1)
            if current_quarter == 4:
                end_date = datetime(today.year, 12, 31)
            else:
                end_date = datetime(today.year, current_quarter * 3 + 1, 1) - timedelta(days=1)
        else:  # year
            start_date = datetime(int(year), 1, 1)
            end_date = datetime(int(year), 12, 31)
        
        # Build the severity filter
        severity_filter = ""
        if severity == 'high' or severity == 'major':
            severity_filter = "AND af.MajorMinor = '1'"  # Major = High
        elif severity == 'medium' or severity == 'minor':
            severity_filter = "AND af.MajorMinor = '0'"  # Minor = Medium
        elif severity == 'low' or severity == 'none':
            severity_filter = "AND (af.MajorMinor IS NULL OR af.MajorMinor = '' OR af.MajorMinor = 'NA')"  # Unspecified = Low/None
        
        # Calculate total non-compliance count
        count_query = f"""
            SELECT COUNT(*) AS non_compliance_count
            FROM audit_findings af
            JOIN compliance c ON af.ComplianceId = c.ComplianceId
            WHERE c.IsRisk = 1
                AND af.AssignedDate BETWEEN %s AND %s
                {severity_filter}
        """
        
        # Get monthly trend data
        monthly_trend_query = f"""
            SELECT 
                DATE_FORMAT(af.AssignedDate, '%%Y-%%m') AS month,
                COUNT(*) AS issue_count
            FROM 
                audit_findings af
            JOIN 
                compliance c ON af.ComplianceId = c.ComplianceId
            WHERE 
                c.IsRisk = 1
                AND af.AssignedDate BETWEEN %s AND %s
                {severity_filter}
            GROUP BY 
                month
            ORDER BY 
                month
        """
        
        # Get severity breakdown
        severity_breakdown_query = """
            SELECT 
                CASE
                    WHEN af.MajorMinor = '1' THEN 'Major'
                    WHEN af.MajorMinor = '0' THEN 'Minor'
                    WHEN af.MajorMinor IS NULL OR af.MajorMinor = '' OR af.MajorMinor = 'NA' THEN 'None'
                    ELSE af.MajorMinor
                END as severity,
                COUNT(*) as count
            FROM 
                audit_findings af
            JOIN 
                compliance c ON af.ComplianceId = c.ComplianceId
            WHERE 
                c.IsRisk = 1
                AND af.AssignedDate BETWEEN %s AND %s
            GROUP BY 
                severity
        """
        
        # Get top impacted controls/areas
        top_areas_query = """
            SELECT 
                c.ComplianceId,
                CASE
                    WHEN sp.SubPolicyName IS NOT NULL THEN sp.SubPolicyName
                    WHEN p.PolicyName IS NOT NULL THEN CONCAT(p.PolicyName, ' Control')
                    ELSE CONCAT('Compliance #', c.ComplianceId)
                END as compliance_name,
                COUNT(*) as issue_count
            FROM 
                audit_findings af
            JOIN 
                compliance c ON af.ComplianceId = c.ComplianceId
            LEFT JOIN
                subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
            LEFT JOIN
                policies p ON sp.PolicyId = p.PolicyId
            WHERE 
                c.IsRisk = 1
                AND af.AssignedDate BETWEEN %s AND %s
            GROUP BY 
                c.ComplianceId, compliance_name
            ORDER BY 
                issue_count DESC
            LIMIT 5
        """
        
        with connection.cursor() as cursor:
            # Get total count
            cursor.execute(count_query, [start_date, end_date])
            result = cursor.fetchone()
            total_count = result[0] if result else 0
            
            # Get monthly trend
            cursor.execute(monthly_trend_query, [start_date, end_date])
            monthly_trend = []
            
            for row in cursor.fetchall():
                month_str, count = row
                if month_str:
                    year, month = map(int, month_str.split('-'))
                    month_date = datetime(year, month, 1)
                    
                    monthly_trend.append({
                        'month': month_date.strftime('%b %Y'),
                        'count': count
                    })
            
            # Get severity breakdown
            cursor.execute(severity_breakdown_query, [start_date, end_date])
            severity_data = []
            
            for row in cursor.fetchall():
                severity, count = row
                
                # Map the severity values to their proper labels - no need to map anymore since we're using the right labels in the query
                severity_data.append({
                    'severity': severity,
                    'count': count
                })
            
            # Get top impacted areas
            cursor.execute(top_areas_query, [start_date, end_date])
            top_areas = []
            
            for row in cursor.fetchall():
                compliance_id, compliance_name, count = row
                
                top_areas.append({
                    'compliance_id': compliance_id,
                    'compliance_name': compliance_name or f'Compliance #{compliance_id}',
                    'count': count
                })
        
        # Calculate trend indicator (comparing to previous period)
        trend_direction = "stable"
        trend_percentage = 0
        
        if period == 'month':
            # Compare to previous month
            prev_start = start_date - timedelta(days=start_date.day)
            prev_end = start_date - timedelta(days=1)
        elif period == 'quarter':
            # Compare to previous quarter
            if current_quarter == 1:
                prev_start = datetime(today.year - 1, 10, 1)
                prev_end = datetime(today.year - 1, 12, 31)
            else:
                prev_start = datetime(today.year, (current_quarter - 2) * 3 + 1, 1)
                prev_end = datetime(today.year, (current_quarter - 1) * 3, 1) - timedelta(days=1)
        else:  # year
            # Compare to previous year
            prev_start = datetime(int(year) - 1, 1, 1)
            prev_end = datetime(int(year) - 1, 12, 31)
        
        # Get previous period count
        prev_period_query = f"""
            SELECT COUNT(*) AS prev_count
            FROM audit_findings af
            JOIN compliance c ON af.ComplianceId = c.ComplianceId
            WHERE c.IsRisk = 1
                AND af.AssignedDate BETWEEN %s AND %s
                {severity_filter}
        """
        
        with connection.cursor() as cursor:
            cursor.execute(prev_period_query, [prev_start, prev_end])
            result = cursor.fetchone()
            prev_count = result[0] if result else 0
            
            if prev_count > 0:
                trend_percentage = round(((total_count - prev_count) / prev_count) * 100, 1)
                if trend_percentage > 5:
                    trend_direction = "up"
                elif trend_percentage < -5:
                    trend_direction = "down"
        
        response = Response({
            'success': True,
            'data': {
                'title': 'Non-Compliance Issues',
                'metrics': {
                    'total_count': total_count,
                    'trend_direction': trend_direction,
                    'trend_percentage': trend_percentage,
                    'selected_severity': severity
                },
                'monthly_trend': monthly_trend,
                'severity_breakdown': severity_data,
                'top_areas': top_areas,
                'period': period,
                'year': year
            }
        })
        
        # Add CORS headers
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        send_log(module="KPI", actionType="GET_NON_COMPLIANCE_ISSUES", description="Fetched non-compliance issues metrics", userId=request.session.get('user_id'))
        
        return response
        
    except Exception as e:
        logger.error(f"Error in get_non_compliance_issues: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
@audit_analytics_required
def get_severity_distribution(request):
    try:
        # Get time period from query params (default to current year)
        period = request.GET.get('period', 'year')
        year = request.GET.get('year', datetime.now().year)
        
        # Calculate date range
        today = timezone.now()
        if period == 'month':
            start_date = datetime(today.year, today.month, 1)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        elif period == 'quarter':
            current_quarter = (today.month - 1) // 3 + 1
            start_date = datetime(today.year, (current_quarter - 1) * 3 + 1, 1)
            if current_quarter == 4:
                end_date = datetime(today.year, 12, 31)
            else:
                end_date = datetime(today.year, current_quarter * 3 + 1, 1) - timedelta(days=1)
        else:  # year
            start_date = datetime(int(year), 1, 1)
            end_date = datetime(int(year), 12, 31)
        
        # Get severity distribution based on MajorMinor column
        severity_query = """
            SELECT 
                CASE
                    WHEN MajorMinor = '1' THEN 'Major'
                    WHEN MajorMinor = '0' THEN 'Minor'
                    WHEN MajorMinor IS NULL OR MajorMinor = '' OR MajorMinor = 'NA' THEN 'None'
                    ELSE MajorMinor
                END as severity_level, 
                COUNT(*) AS count
            FROM 
                audit_findings af
            JOIN 
                compliance c ON af.ComplianceId = c.ComplianceId
            WHERE 
                c.IsRisk = 1
                AND af.AssignedDate BETWEEN %s AND %s
            GROUP BY 
                severity_level
            ORDER BY 
                FIELD(severity_level, 'Major', 'Minor', 'None')
        """
        
        # Get severity trend over time
        trend_query = """
            SELECT 
                DATE_FORMAT(af.AssignedDate, '%%Y-%%m') AS month,
                CASE
                    WHEN MajorMinor = '1' THEN 'Major'
                    WHEN MajorMinor = '0' THEN 'Minor'
                    WHEN MajorMinor IS NULL OR MajorMinor = '' OR MajorMinor = 'NA' THEN 'None'
                    ELSE MajorMinor
                END as severity_level,
                COUNT(*) AS count
            FROM 
                audit_findings af
            JOIN 
                compliance c ON af.ComplianceId = c.ComplianceId
            WHERE 
                c.IsRisk = 1
                AND af.AssignedDate BETWEEN %s AND %s
            GROUP BY 
                month, severity_level
            ORDER BY 
                month, FIELD(severity_level, 'Major', 'Minor', 'None')
        """
        
        # Get framework distribution by severity
        framework_query = """
            SELECT 
                f.FrameworkName,
                CASE
                    WHEN MajorMinor = '1' THEN 'Major'
                    WHEN MajorMinor = '0' THEN 'Minor'
                    WHEN MajorMinor IS NULL OR MajorMinor = '' OR MajorMinor = 'NA' THEN 'None'
                    ELSE MajorMinor
                END as severity_level,
                COUNT(*) AS count
            FROM 
                audit_findings af
            JOIN 
                compliance c ON af.ComplianceId = c.ComplianceId
            JOIN 
                audit a ON af.AuditId = a.AuditId
            LEFT JOIN 
                frameworks f ON a.FrameworkId = f.FrameworkId
            WHERE 
                c.IsRisk = 1
                AND af.AssignedDate BETWEEN %s AND %s
            GROUP BY 
                f.FrameworkName, severity_level
            ORDER BY 
                COUNT(*) DESC, f.FrameworkName
            LIMIT 15
        """
        
        with connection.cursor() as cursor:
            # Get severity distribution
            cursor.execute(severity_query, [start_date, end_date])
            severity_data = []
            
            # Define color map for severity levels
            color_map = {
                'Major': '#d32f2f',    # Deep red
                'Minor': '#ff9800',    # Orange
                'None': '#9e9e9e'  # Grey
            }
            
            total_issues = 0
            for row in cursor.fetchall():
                severity, count = row
                total_issues += count
                
                # Get color for the severity level
                color = color_map.get(severity, '#9e9e9e')
                
                severity_data.append({
                    'severity': severity,
                    'count': count,
                    'color': color
                })
            
            # Get severity trend
            cursor.execute(trend_query, [start_date, end_date])
            trend_data = {}
            
            for row in cursor.fetchall():
                month_str, severity, count = row
                
                if month_str not in trend_data:
                    trend_data[month_str] = {}
                
                trend_data[month_str][severity] = count
            
            # Convert trend data to array format
            trend_array = []
            for month_str, severities in trend_data.items():
                if month_str:
                    year, month = map(int, month_str.split('-'))
                    month_date = datetime(year, month, 1)
                    month_name = month_date.strftime('%b %Y')
                    
                    # Ensure all severity levels are represented
                    month_data = {
                        'month': month_name,
                        'Major': severities.get('Major', 0),
                        'Minor': severities.get('Minor', 0),
                        'None': severities.get('None', 0)
                    }
                    trend_array.append(month_data)
            
            # Sort by date
            trend_array.sort(key=lambda x: datetime.strptime(x['month'], '%b %Y'))
            
            # Get framework distribution
            cursor.execute(framework_query, [start_date, end_date])
            framework_data = {}
            
            for row in cursor.fetchall():
                framework, severity, count = row
                
                # Use 'Unknown' for null framework names
                framework_name = framework if framework else 'Unknown'
                
                if framework_name not in framework_data:
                    framework_data[framework_name] = {}
                
                framework_data[framework_name][severity] = count
            
            # Convert framework data to array format
            framework_array = []
            for framework_name, severities in framework_data.items():
                # Ensure all severity levels are represented
                framework_item = {
                    'framework': framework_name,
                    'Major': severities.get('Major', 0),
                    'Minor': severities.get('Minor', 0),
                    'None': severities.get('None', 0),
                    'total': sum(severities.values())
                }
                framework_array.append(framework_item)
            
            # Sort by total count
            framework_array.sort(key=lambda x: x['total'], reverse=True)
        
        # Calculate most common severity
        most_common = max(severity_data, key=lambda x: x['count']) if severity_data else None
        
        # Count of major issues (considered critical for this purpose)
        major_count = next((item['count'] for item in severity_data if item['severity'] == 'Major'), 0)
        
        response = Response({
            'success': True,
            'data': {
                'title': 'Severity of Issues',
                'metrics': {
                    'total_issues': total_issues,
                    'most_common': most_common['severity'] if most_common else 'None',
                    'most_common_count': most_common['count'] if most_common else 0,
                    'major_count': major_count,
                    'minor_count': next((item['count'] for item in severity_data if item['severity'] == 'Minor'), 0)
                },
                'severity_distribution': severity_data,
                'severity_trend': trend_array,
                'framework_distribution': framework_array,
                'period': period,
                'year': year
            }
        })
        
        # Add CORS headers
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        send_log(module="KPI", actionType="GET_SEVERITY_DISTRIBUTION", description="Fetched severity distribution metrics", userId=request.session.get('user_id'))
        
        return response
        
    except Exception as e:
        logger.error(f"Error in get_severity_distribution: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
@audit_analytics_required
def get_findings_closure_rate(request):
    try:
        # Get time period from query params (default to current year)
        period = request.GET.get('period', 'year')
        year = request.GET.get('year', datetime.now().year)
        
        # Calculate date range
        today = timezone.now()
        if period == 'month':
            start_date = datetime(today.year, today.month, 1)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        elif period == 'quarter':
            current_quarter = (today.month - 1) // 3 + 1
            start_date = datetime(today.year, (current_quarter - 1) * 3 + 1, 1)
            if current_quarter == 4:
                end_date = datetime(today.year, 12, 31)
            else:
                end_date = datetime(today.year, current_quarter * 3 + 1, 1) - timedelta(days=1)
        else:  # year
            start_date = datetime(int(year), 1, 1)
            end_date = datetime(int(year), 12, 31)
        
        # Calculate overall closure rate
        closure_rate_query = """
            SELECT
                ROUND(
                    (SELECT COUNT(*) FROM audit_findings 
                     WHERE ReviewStatus = '1' 
                     AND ReviewDate BETWEEN %s AND %s) * 100.0 /
                    NULLIF((SELECT COUNT(*) FROM audit_findings 
                           WHERE AssignedDate BETWEEN %s AND %s), 0),
                    2
                ) AS closure_rate_percent,
                (SELECT COUNT(*) FROM audit_findings 
                 WHERE ReviewStatus = '1' 
                 AND ReviewDate BETWEEN %s AND %s) AS closed_count,
                (SELECT COUNT(*) FROM audit_findings 
                 WHERE AssignedDate BETWEEN %s AND %s) AS opened_count
        """
        
        # Calculate monthly closure rates for trend
        monthly_trend_query = """
            SELECT
                DATE_FORMAT(month_date, '%%Y-%%m') AS month,
                closed_count,
                opened_count,
                ROUND(
                    closed_count * 100.0 / NULLIF(opened_count, 0),
                    2
                ) AS closure_rate
            FROM (
                SELECT
                    DATE(DATE_FORMAT(af.AssignedDate, '%%Y-%%m-01')) AS month_date,
                    SUM(CASE WHEN af.ReviewStatus = '1' AND af.ReviewDate BETWEEN %s AND %s THEN 1 ELSE 0 END) AS closed_count,
                    COUNT(*) AS opened_count
                FROM
                    audit_findings af
                WHERE
                    af.AssignedDate BETWEEN %s AND %s
                GROUP BY
                    month_date
            ) AS monthly_data
            ORDER BY
                month_date
        """
        
        # Get average time to close
        avg_closure_time_query = """
            SELECT
                AVG(DATEDIFF(ReviewDate, AssignedDate)) AS avg_days_to_close
            FROM
                audit_findings
            WHERE
                ReviewStatus = '1'
                AND ReviewDate IS NOT NULL
                AND AssignedDate IS NOT NULL
                AND ReviewDate BETWEEN %s AND %s
        """
        
        # Get top 5 fastest closed findings
        fastest_closed_query = """
            SELECT
                af.AuditFindingsId,
                af.AuditId,
                DATEDIFF(af.ReviewDate, af.AssignedDate) AS days_to_close,
                a.Status AS audit_status,
                f.FrameworkName,
                p.PolicyName
            FROM
                audit_findings af
            JOIN
                audit a ON af.AuditId = a.AuditId
            LEFT JOIN
                frameworks f ON a.FrameworkId = f.FrameworkId
            LEFT JOIN
                policies p ON a.PolicyId = p.PolicyId
            WHERE
                af.ReviewStatus = '1'
                AND af.ReviewDate IS NOT NULL
                AND af.AssignedDate IS NOT NULL
                AND af.ReviewDate BETWEEN %s AND %s
            ORDER BY
                days_to_close ASC
            LIMIT 5
        """
        
        with connection.cursor() as cursor:
            # Get overall closure rate
            cursor.execute(closure_rate_query, [
                start_date, end_date, 
                start_date, end_date,
                start_date, end_date,
                start_date, end_date
            ])
            result = cursor.fetchone()
            
            closure_rate = float(result[0]) if result[0] else 0
            closed_count = result[1] if result[1] else 0
            opened_count = result[2] if result[2] else 0
            
            # Get monthly trend data
            cursor.execute(monthly_trend_query, [
                start_date, end_date,
                start_date, end_date
            ])
            monthly_trend = []
            
            for row in cursor.fetchall():
                month_str, closed, opened, rate = row
                if month_str:
                    year, month = map(int, month_str.split('-'))
                    month_date = datetime(year, month, 1)
                    
                    monthly_trend.append({
                        'month': month_date.strftime('%b %Y'),
                        'closed_count': closed,
                        'opened_count': opened,
                        'closure_rate': float(rate) if rate else 0
                    })
            
            # Get average time to close
            cursor.execute(avg_closure_time_query, [start_date, end_date])
            avg_days_result = cursor.fetchone()
            avg_days_to_close = round(float(avg_days_result[0]), 1) if avg_days_result[0] else 0
            
            # Get fastest closed findings
            cursor.execute(fastest_closed_query, [start_date, end_date])
            fastest_closed = []
            
            for row in cursor.fetchall():
                finding_id, audit_id, days_to_close, audit_status, framework, policy = row
                
                fastest_closed.append({
                    'finding_id': finding_id,
                    'audit_id': audit_id,
                    'days_to_close': days_to_close,
                    'audit_status': audit_status or 'Unknown',
                    'framework': framework or 'Unknown',
                    'policy': policy or 'Unknown'
                })
        
        # Determine performance rating
        if closure_rate >= 90:
            rating = 'Excellent'
            color = 'success'
        elif closure_rate >= 75:
            rating = 'Good'
            color = 'info'
        elif closure_rate >= 50:
            rating = 'Fair'
            color = 'warning'
        else:
            rating = 'Poor'
            color = 'error'
        
        response = Response({
            'success': True,
            'data': {
                'title': 'Findings Closure Rate',
                'metrics': {
                    'closure_rate': closure_rate,
                    'closed_count': closed_count,
                    'opened_count': opened_count,
                    'avg_days_to_close': avg_days_to_close,
                    'rating': rating,
                    'color': color
                },
                'monthly_trend': monthly_trend,
                'fastest_closed': fastest_closed,
                'period': period,
                'year': year
            }
        })
        
        # Add CORS headers
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        send_log(module="KPI", actionType="GET_FINDINGS_CLOSURE_RATE", description="Fetched findings closure rate metrics", userId=request.session.get('user_id'))
        
        return response
        
    except Exception as e:
        logger.error(f"Error in get_findings_closure_rate: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
@audit_analytics_required
def get_evidence_completion(request):
    try:
        # Get audit ID filter if provided
        audit_id = request.GET.get('audit_id', None)
        
        # Base query to count findings with and without evidence
        base_query = """
            SELECT 
                COUNT(CASE WHEN af.Evidence IS NOT NULL AND TRIM(af.Evidence) != '' THEN 1 END) AS evidence_collected,
                COUNT(*) AS total_findings,
                ROUND(
                    (COUNT(CASE WHEN af.Evidence IS NOT NULL AND TRIM(af.Evidence) != '' THEN 1 END) * 100.0) / 
                    NULLIF(COUNT(*), 0),
                    2
                ) AS completion_percentage
            FROM 
                audit_findings af
            JOIN
                audit a ON af.AuditId = a.AuditId
            WHERE 
                a.Status = 'Completed'  -- Only include completed audits
        """
        
        # Add audit filter if provided
        audit_filter = ""
        params = []
        if audit_id:
            audit_filter = " AND af.AuditId = %s"
            params.append(audit_id)
        
        # Execute the query
        with connection.cursor() as cursor:
            # Add WHERE clause if audit filter is provided
            if audit_filter:
                query = base_query + audit_filter
            else:
                query = base_query
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            evidence_collected, total_findings, completion_percentage = (
                result[0] if result[0] is not None else 0,
                result[1] if result[1] is not None else 0,
                float(result[2]) if result[2] is not None else 0
            )
            
            # Get breakdown by audit if no specific audit requested
            audit_breakdown = []
            if not audit_id:
                audit_breakdown_query = """
                    SELECT 
                        af.AuditId, 
                        a.FrameworkId,
                        f.FrameworkName,
                        COUNT(CASE WHEN af.Evidence IS NOT NULL AND TRIM(af.Evidence) != '' THEN 1 END) AS evidence_collected,
                        COUNT(*) AS total_findings,
                        ROUND(
                            (COUNT(CASE WHEN af.Evidence IS NOT NULL AND TRIM(af.Evidence) != '' THEN 1 END) * 100.0) / 
                            NULLIF(COUNT(*), 0),
                            2
                        ) AS completion_percentage
                    FROM 
                        audit_findings af
                    JOIN
                        audit a ON af.AuditId = a.AuditId
                    LEFT JOIN
                        frameworks f ON a.FrameworkId = f.FrameworkId
                    WHERE 
                        a.Status = 'Completed'  -- Only include completed audits
                    GROUP BY 
                        af.AuditId, a.FrameworkId, f.FrameworkName
                    HAVING 
                        total_findings > 0  -- Only include audits with findings
                    ORDER BY 
                        completion_percentage DESC
                    LIMIT 10
                """
                cursor.execute(audit_breakdown_query)
                for row in cursor.fetchall():
                    audit_id, framework_id, framework_name, audit_collected, audit_total, audit_percentage = row
                    audit_breakdown.append({
                        'audit_id': audit_id,
                        'framework_id': framework_id,
                        'framework_name': framework_name or 'Unknown',
                        'evidence_collected': audit_collected,
                        'total_findings': audit_total,
                        'completion_percentage': float(audit_percentage) if audit_percentage else 0
                    })
            
            # Get details of evidence if specific audit requested
            evidence_details = []
            if audit_id:
                evidence_details_query = """
                    SELECT 
                        af.AuditFindingsId,
                        af.ComplianceId,
                        af.Evidence,
                        CASE WHEN af.Evidence IS NOT NULL AND TRIM(af.Evidence) != '' THEN 1 ELSE 0 END AS has_evidence
                    FROM 
                        audit_findings af
                    JOIN
                        audit a ON af.AuditId = a.AuditId
                    WHERE 
                        af.AuditId = %s
                        AND a.Status = 'Completed'  -- Only include completed audits
                    ORDER BY 
                        af.ComplianceId
                """
                cursor.execute(evidence_details_query, [audit_id])
                for row in cursor.fetchall():
                    finding_id, compliance_id, evidence, has_evidence = row
                    evidence_details.append({
                        'finding_id': finding_id,
                        'compliance_id': compliance_id,
                        'evidence': evidence or '',
                        'has_evidence': has_evidence == 1
                    })
        
        # Determine rating based on completion percentage
        if completion_percentage >= 90:
            rating = 'Excellent'
            color = 'success'
        elif completion_percentage >= 70:
            rating = 'Good'
            color = 'info'
        elif completion_percentage >= 50:
            rating = 'Fair'
            color = 'warning'
        else:
            rating = 'Needs Improvement'
            color = 'error'
        
        response = Response({
            'success': True,
            'data': {
                'title': 'Evidence Collection',
                'metrics': {
                    'evidence_collected': evidence_collected,
                    'total_findings': total_findings,
                    'completion_percentage': completion_percentage,
                    'rating': rating,
                    'color': color
                },
                'audit_breakdown': audit_breakdown,
                'evidence_details': evidence_details,
                'filtered_audit_id': audit_id
            }
        })
        
        # Add CORS headers
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        send_log(module="KPI", actionType="GET_EVIDENCE_COMPLETION", description="Fetched evidence completion metrics", userId=request.session.get('user_id'))
        
        return response
        
    except Exception as e:
        logger.error(f"Error in get_evidence_completion: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
@audit_analytics_required
def get_report_timeliness(request):
    try:
        # Get time period from query params (default to current year)
        period = request.GET.get('period', 'year')
        year = request.GET.get('year', datetime.now().year)
        
        # Calculate date range
        today = timezone.now()
        if period == 'month':
            start_date = datetime(today.year, today.month, 1)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        elif period == 'quarter':
            current_quarter = (today.month - 1) // 3 + 1
            start_date = datetime(today.year, (current_quarter - 1) * 3 + 1, 1)
            if current_quarter == 4:
                end_date = datetime(today.year, 12, 31)
            else:
                end_date = datetime(today.year, current_quarter * 3 + 1, 1) - timedelta(days=1)
        else:  # year
            start_date = datetime(int(year), 1, 1)
            end_date = datetime(int(year), 12, 31)
        
        # Calculate report timeliness metrics
        # Only include completed audits with both DueDate and CompletionDate
        timeliness_query = """
            SELECT
                AVG(DATEDIFF(CompletionDate, DueDate)) AS avg_days_difference,
                ROUND(SUM(CASE WHEN CompletionDate <= DueDate THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS percent_on_time,
                COUNT(*) AS total_reports,
                SUM(CASE WHEN CompletionDate <= DueDate THEN 1 ELSE 0 END) AS on_time_count,
                SUM(CASE WHEN CompletionDate > DueDate THEN 1 ELSE 0 END) AS late_count
            FROM
                audit
            WHERE
                DueDate IS NOT NULL
                AND CompletionDate IS NOT NULL
                AND DueDate BETWEEN %s AND %s
        """
        
        # Get histogram data - group by days difference ranges
        histogram_query = """
            SELECT
                CASE
                    WHEN DATEDIFF(CompletionDate, DueDate) <= -7 THEN 'early_7plus'
                    WHEN DATEDIFF(CompletionDate, DueDate) BETWEEN -6 AND -1 THEN 'early_1to6'
                    WHEN DATEDIFF(CompletionDate, DueDate) = 0 THEN 'on_time'
                    WHEN DATEDIFF(CompletionDate, DueDate) BETWEEN 1 AND 7 THEN 'late_1to7'
                    WHEN DATEDIFF(CompletionDate, DueDate) BETWEEN 8 AND 14 THEN 'late_8to14'
                    ELSE 'late_15plus'
                END AS timeliness_category,
                COUNT(*) AS count
            FROM
                audit
            WHERE
                DueDate IS NOT NULL
                AND CompletionDate IS NOT NULL
                AND DueDate BETWEEN %s AND %s
            GROUP BY
                timeliness_category
            ORDER BY
                FIELD(timeliness_category, 'early_7plus', 'early_1to6', 'on_time', 'late_1to7', 'late_8to14', 'late_15plus')
        """
        
        # Get list of late reports for drill-down
        late_reports_query = """
            SELECT
                a.AuditId,
                a.FrameworkId,
                a.AssignedDate,
                a.DueDate,
                a.CompletionDate,
                a.Status,
                DATEDIFF(a.CompletionDate, a.DueDate) AS days_late,
                COALESCE(f.FrameworkName, 'Unknown') AS framework_name
            FROM
                audit a
            LEFT JOIN
                frameworks f ON a.FrameworkId = f.FrameworkId
            WHERE
                a.DueDate IS NOT NULL
                AND a.CompletionDate IS NOT NULL
                AND a.CompletionDate > a.DueDate
                AND a.DueDate BETWEEN %s AND %s
            ORDER BY
                days_late DESC
            LIMIT 10
        """
        
        # Get trend data over months
        trend_query = """
            SELECT
                DATE_FORMAT(DueDate, '%%Y-%%m') AS month,
                ROUND(SUM(CASE WHEN CompletionDate <= DueDate THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS percent_on_time,
                COUNT(*) AS total_reports
            FROM
                audit
            WHERE
                DueDate IS NOT NULL
                AND CompletionDate IS NOT NULL
                AND DueDate BETWEEN %s AND %s
            GROUP BY
                month
            ORDER BY
                month
        """
        
        with connection.cursor() as cursor:
            # Get overall timeliness metrics
            cursor.execute(timeliness_query, [start_date, end_date])
            result = cursor.fetchone()
            
            avg_days_difference = float(result[0]) if result[0] is not None else 0
            percent_on_time = float(result[1]) if result[1] is not None else 0
            total_reports = int(result[2]) if result[2] is not None else 0
            on_time_count = int(result[3]) if result[3] is not None else 0
            late_count = int(result[4]) if result[4] is not None else 0
            
            # Get histogram data
            cursor.execute(histogram_query, [start_date, end_date])
            histogram_data = []
            
            # Initialize all categories with zero to ensure all are present
            categories = {
                'early_7plus': {'label': 'Very Early (7+ days)', 'count': 0, 'color': '#4CAF50'},
                'early_1to6': {'label': 'Early (1-6 days)', 'count': 0, 'color': '#8BC34A'},
                'on_time': {'label': 'On Time', 'count': 0, 'color': '#03A9F4'},
                'late_1to7': {'label': 'Late (1-7 days)', 'count': 0, 'color': '#FFC107'},
                'late_8to14': {'label': 'Late (8-14 days)', 'count': 0, 'color': '#FF9800'},
                'late_15plus': {'label': 'Very Late (15+ days)', 'count': 0, 'color': '#F44336'}
            }
            
            for row in cursor.fetchall():
                category, count = row
                if category in categories:
                    categories[category]['count'] = count
            
            # Convert dictionary to ordered list
            for key, data in categories.items():
                histogram_data.append({
                    'category': key,
                    'label': data['label'],
                    'count': data['count'],
                    'color': data['color'],
                    'percentage': round((data['count'] / total_reports) * 100, 2) if total_reports > 0 else 0
                })
            
            # Get late reports
            cursor.execute(late_reports_query, [start_date, end_date])
            late_reports = []
            
            for row in cursor.fetchall():
                audit_id, framework_id, assigned_date, due_date, completion_date, status, days_late, framework_name = row
                
                late_reports.append({
                    'audit_id': audit_id,
                    'framework_id': framework_id,
                    'framework_name': framework_name,
                    'assigned_date': assigned_date.strftime('%Y-%m-%d') if assigned_date else None,
                    'due_date': due_date.strftime('%Y-%m-%d') if due_date else None,
                    'completion_date': completion_date.strftime('%Y-%m-%d') if completion_date else None,
                    'status': status,
                    'days_late': days_late
                })
            
            # Get trend data
            cursor.execute(trend_query, [start_date, end_date])
            trend_data = []
            
            for row in cursor.fetchall():
                month_str, month_percent, month_total = row
                if month_str:
                    year, month = map(int, month_str.split('-'))
                    month_date = datetime(year, month, 1)
                    
                    trend_data.append({
                        'month': month_date.strftime('%b %Y'),
                        'percent_on_time': float(month_percent) if month_percent else 0,
                        'total_reports': month_total
                    })
        
        # Determine timeliness rating
        if percent_on_time >= 90:
            rating = 'Excellent'
            color = 'success'
        elif percent_on_time >= 75:
            rating = 'Good'
            color = 'info'
        elif percent_on_time >= 60:
            rating = 'Fair'
            color = 'warning'
        else:
            rating = 'Needs Improvement'
            color = 'error'
        
        response = Response({
            'success': True,
            'data': {
                'title': 'Audit Report Timeliness',
                'metrics': {
                    'avg_days_difference': avg_days_difference,
                    'percent_on_time': percent_on_time,
                    'total_reports': total_reports,
                    'on_time_count': on_time_count,
                    'late_count': late_count,
                    'rating': rating,
                    'color': color
                },
                'histogram': histogram_data,
                'late_reports': late_reports,
                'trend_data': trend_data,
                'period': period,
                'year': year
            }
        })
        
        # Add CORS headers
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        send_log(module="KPI", actionType="GET_REPORT_TIMELINESS", description="Fetched audit report timeliness metrics", userId=request.session.get('user_id'))
        
        return response
        
    except Exception as e:
        logger.error(f"Error in get_report_timeliness: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
@audit_analytics_required
def get_compliance_readiness(request):
    try:
        # Get framework or policy filter if provided
        framework_id = request.GET.get('framework_id', None)
        policy_id = request.GET.get('policy_id', None)
        
        # Base query for counts - determine compliance status based on ActiveInactive field
        # ActiveInactive with 'Active' means the control is defined and ready for testing
        # We'll use IsRisk to determine if control is implemented or not (IsRisk=0 means implemented/compliant)
        base_query = """
            SELECT 
                COUNT(*) AS total_defined,
                SUM(CASE WHEN IsRisk = 0 THEN 1 ELSE 0 END) AS implemented_count,
                ROUND(
                    SUM(CASE WHEN IsRisk = 0 THEN 1 ELSE 0 END) * 100.0 / 
                    NULLIF(COUNT(*), 0),
                    2
                ) AS readiness_percentage
            FROM 
                compliance
            WHERE 
                ActiveInactive = 'Active'
        """
        
        # Add framework or policy filter if provided
        where_clause = " AND ActiveInactive = 'Active'"
        params = []
        
        if framework_id:
            # Join to get the framework
            base_query = """
                SELECT 
                    COUNT(*) AS total_defined,
                    SUM(CASE WHEN c.IsRisk = 0 THEN 1 ELSE 0 END) AS implemented_count,
                    ROUND(
                        SUM(CASE WHEN c.IsRisk = 0 THEN 1 ELSE 0 END) * 100.0 / 
                        NULLIF(COUNT(*), 0),
                        2
                    ) AS readiness_percentage
                FROM 
                    compliance c
                JOIN
                    lastchecklistitemverified lciv ON c.ComplianceId = lciv.ComplianceId
                WHERE 
                    c.ActiveInactive = 'Active'
                    AND lciv.FrameworkId = %s
            """
            params.append(framework_id)
        
        elif policy_id:
            # Join to get the policy
            base_query = """
                SELECT 
                    COUNT(*) AS total_defined,
                    SUM(CASE WHEN c.IsRisk = 0 THEN 1 ELSE 0 END) AS implemented_count,
                    ROUND(
                        SUM(CASE WHEN c.IsRisk = 0 THEN 1 ELSE 0 END) * 100.0 / 
                        NULLIF(COUNT(*), 0),
                        2
                    ) AS readiness_percentage
                FROM 
                    compliance c
                JOIN
                    lastchecklistitemverified lciv ON c.ComplianceId = lciv.ComplianceId
                WHERE 
                    c.ActiveInactive = 'Active'
                    AND lciv.PolicyId = %s
            """
            params.append(policy_id)
        
        # Get framework breakdown data
        framework_query = """
            SELECT 
                f.FrameworkId,
                f.FrameworkName,
                COUNT(*) AS total_defined,
                SUM(CASE WHEN c.IsRisk = 0 THEN 1 ELSE 0 END) AS implemented_count,
                ROUND(
                    SUM(CASE WHEN c.IsRisk = 0 THEN 1 ELSE 0 END) * 100.0 / 
                    NULLIF(COUNT(*), 0),
                    2
                ) AS readiness_percentage
            FROM 
                compliance c
            JOIN
                lastchecklistitemverified lciv ON c.ComplianceId = lciv.ComplianceId
            JOIN
                frameworks f ON lciv.FrameworkId = f.FrameworkId
            WHERE 
                c.ActiveInactive = 'Active'
            GROUP BY 
                f.FrameworkId, f.FrameworkName
            ORDER BY 
                readiness_percentage DESC, f.FrameworkName
        """
        
        # Get policy breakdown data
        policy_query = """
            SELECT 
                p.PolicyId,
                p.PolicyName,
                COUNT(*) AS total_defined,
                SUM(CASE WHEN c.IsRisk = 0 THEN 1 ELSE 0 END) AS implemented_count,
                ROUND(
                    SUM(CASE WHEN c.IsRisk = 0 THEN 1 ELSE 0 END) * 100.0 / 
                    NULLIF(COUNT(*), 0),
                    2
                ) AS readiness_percentage
            FROM 
                compliance c
            JOIN
                lastchecklistitemverified lciv ON c.ComplianceId = lciv.ComplianceId
            JOIN
                policies p ON lciv.PolicyId = p.PolicyId
            WHERE 
                c.ActiveInactive = 'Active'
            GROUP BY 
                p.PolicyId, p.PolicyName
            ORDER BY 
                readiness_percentage DESC, p.PolicyName
        """
        
        # Get criticality breakdown data
        criticality_query = """
            SELECT 
                COALESCE(c.Criticality, 'Undefined') AS criticality_level,
                COUNT(*) AS total_defined,
                SUM(CASE WHEN c.IsRisk = 0 THEN 1 ELSE 0 END) AS implemented_count,
                ROUND(
                    SUM(CASE WHEN c.IsRisk = 0 THEN 1 ELSE 0 END) * 100.0 / 
                    NULLIF(COUNT(*), 0),
                    2
                ) AS readiness_percentage
            FROM 
                compliance c
            WHERE 
                c.ActiveInactive = 'Active'
            GROUP BY 
                criticality_level
            ORDER BY 
                FIELD(criticality_level, 'Critical', 'High', 'Medium', 'Low', 'Undefined')
        """
        
        with connection.cursor() as cursor:
            # Get overall metrics
            cursor.execute(base_query, params)
            result = cursor.fetchone()
            
            if result:
                total_defined, implemented_count, readiness_percentage = (
                    result[0] if result[0] is not None else 0,
                    result[1] if result[1] is not None else 0,
                    float(result[2]) if result[2] is not None else 0
                )
            else:
                total_defined = implemented_count = 0
                readiness_percentage = 0
            
            # Get framework breakdown
            cursor.execute(framework_query)
            frameworks = []
            
            for row in cursor.fetchall():
                framework_id, framework_name, fw_total, fw_implemented, fw_percentage = row
                frameworks.append({
                    'framework_id': framework_id,
                    'name': framework_name or 'Unknown',
                    'total_defined': fw_total,
                    'implemented_count': fw_implemented,
                    'readiness_percentage': float(fw_percentage) if fw_percentage else 0
                })
            
            # Get policy breakdown
            cursor.execute(policy_query)
            policies = []
            
            for row in cursor.fetchall():
                policy_id, policy_name, pol_total, pol_implemented, pol_percentage = row
                policies.append({
                    'policy_id': policy_id,
                    'name': policy_name or 'Unknown',
                    'total_defined': pol_total,
                    'implemented_count': pol_implemented,
                    'readiness_percentage': float(pol_percentage) if pol_percentage else 0
                })
            
            # Get criticality breakdown
            cursor.execute(criticality_query)
            criticality_breakdown = []
            
            for row in cursor.fetchall():
                criticality, crit_total, crit_implemented, crit_percentage = row
                criticality_breakdown.append({
                    'criticality': criticality,
                    'total_defined': crit_total,
                    'implemented_count': crit_implemented,
                    'readiness_percentage': float(crit_percentage) if crit_percentage else 0
                })
        
        # Determine rating based on readiness percentage
        if readiness_percentage >= 90:
            rating = 'Excellent'
            color = 'success'
        elif readiness_percentage >= 75:
            rating = 'Good'
            color = 'info'
        elif readiness_percentage >= 50:
            rating = 'Fair'
            color = 'warning'
        else:
            rating = 'Needs Improvement'
            color = 'error'
        
        response = Response({
            'success': True,
            'data': {
                'title': 'Compliance Readiness',
                'metrics': {
                    'total_defined': total_defined,
                    'implemented_count': implemented_count,
                    'readiness_percentage': readiness_percentage,
                    'rating': rating,
                    'color': color
                },
                'frameworks': frameworks,
                'policies': policies,
                'criticality_breakdown': criticality_breakdown,
                'filtered_framework_id': framework_id,
                'filtered_policy_id': policy_id
            }
        })
        
        # Add CORS headers
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        send_log(module="KPI", actionType="GET_COMPLIANCE_READINESS", description="Fetched compliance readiness metrics", userId=request.session.get('user_id'))
        
        return response
        
    except Exception as e:
        logger.error(f"Error in get_compliance_readiness: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def debug_mttd_calculation(request):
    """
    Debug endpoint to compare MTTD calculation with direct database query
    """
    print("debug_mttd_calculation called")
    
    from django.apps import apps
    from django.http import JsonResponse
    
    try:
        # Get the Incident model from the app registry
        Incident = apps.get_model('grc', 'Incident')
        
        # Method 1: Direct database query (like your MySQL query)
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT AVG(ABS(TIMESTAMPDIFF(SECOND, CreatedAt, IdentifiedAt)) / 60) AS MTTD_minutes
                FROM grc.incidents
                WHERE CreatedAt IS NOT NULL
                AND IdentifiedAt IS NOT NULL
                AND IdentifiedAt >= CreatedAt
                AND CreatedAt BETWEEN '2025-01-01' AND '2025-07-25'
            """)
            db_result = cursor.fetchone()
            db_mttd = db_result[0] if db_result else 0
        
        # Method 2: Django ORM calculation (like the current API)
        incidents = Incident.objects.filter(
            IdentifiedAt__isnull=False,
            CreatedAt__isnull=False
        ).filter(
            IdentifiedAt__gte=F('CreatedAt')  # Only include valid time differences
        ).filter(
            CreatedAt__gte='2025-01-01',
            CreatedAt__lte='2025-07-25'
        )
        
        all_incidents = list(incidents.values('IncidentId', 'CreatedAt', 'IdentifiedAt'))
        
        django_total_minutes = 0
        incident_details = []
        
        for incident in all_incidents:
            created = incident['CreatedAt']
            identified = incident['IdentifiedAt']
            diff_seconds = abs((identified - created).total_seconds())
            minutes = diff_seconds / 60
            django_total_minutes += minutes
            
            incident_details.append({
                'id': incident['IncidentId'],
                'created': created.isoformat(),
                'identified': identified.isoformat(),
                'minutes': round(minutes, 2)
            })
        
        django_mttd = round(django_total_minutes / len(all_incidents), 1) if all_incidents else 0
        
        # Method 3: Check for any data inconsistencies
        data_issues = []
        for incident in all_incidents:
            created = incident['CreatedAt']
            identified = incident['IdentifiedAt']
            
            if created > identified:
                data_issues.append({
                    'id': incident['IncidentId'],
                    'created': created.isoformat(),
                    'identified': identified.isoformat(),
                    'issue': 'CreatedAt is after IdentifiedAt'
                })
        
        response_data = {
            'database_query_mttd': db_mttd,
            'django_calculation_mttd': django_mttd,
            'difference': abs(db_mttd - django_mttd),
            'total_incidents_processed': len(all_incidents),
            'data_issues_count': len(data_issues),
            'sample_incidents': incident_details[:10],
            'data_issues': data_issues[:5],
            'debug_info': {
                'django_total_minutes': django_total_minutes,
                'date_range': '2025-01-01 to 2025-07-25',
                'timestamp': timezone.now().isoformat()
            }
        }
        
        print(f"Database query MTTD: {db_mttd}")
        print(f"Django calculation MTTD: {django_mttd}")
        print(f"Difference: {abs(db_mttd - django_mttd)}")
        print(f"Total incidents: {len(all_incidents)}")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"Error in debug_mttd_calculation: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'error': str(e),
            'debug_info': {
                'error_details': str(e),
                'timestamp': timezone.now().isoformat()
            }
        }, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def generate_sample_audit_data(request):
    """
    Generate sample audit data for testing KPI functions
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        import random
        
        # Get or create a test user
        test_user, created = Users.objects.get_or_create(
            UserName='test_auditor',
            defaults={
                'Email': 'test@example.com',
                'FirstName': 'Test',
                'LastName': 'Auditor',
                'IsActive': 'Y',
                'DepartmentId': '1'
            }
        )
        
        # Get or create a test framework
        test_framework, created = Framework.objects.get_or_create(
            FrameworkName='Test Framework',
            defaults={
                'CurrentVersion': 1.0,
                'FrameworkDescription': 'Test framework for KPI testing',
                'CreatedByName': 'System',
                'CreatedByDate': timezone.now().date(),
                'Reviewer': 'System',
                'ActiveInactive': 'Active'
            }
        )
        
        # Get or create a test policy
        test_policy, created = Policy.objects.get_or_create(
            PolicyName='Test Policy',
            defaults={
                'FrameworkId': test_framework,
                'CurrentVersion': '1.0',
                'Status': 'Active',
                'PolicyDescription': 'Test policy for KPI testing',
                'StartDate': timezone.now().date(),
                'CreatedByName': 'System',
                'CreatedByDate': timezone.now().date(),
                'ActiveInactive': 'Active',
                'Reviewer': 'System'
            }
        )
        
        # Get or create a test subpolicy
        test_subpolicy, created = SubPolicy.objects.get_or_create(
            SubPolicyName='Test SubPolicy',
            defaults={
                'PolicyId': test_policy,
                'CreatedByName': 'System',
                'CreatedByDate': timezone.now().date(),
                'Identifier': 'TEST-001',
                'Description': 'Test subpolicy for KPI testing',
                'Status': 'Active'
            }
        )
        
        # Get or create test compliance items
        test_compliances = []
        for i in range(5):
            compliance, created = Compliance.objects.get_or_create(
                ComplianceTitle=f'Test Compliance {i+1}',
                defaults={
                    'SubPolicy': test_subpolicy,
                    'ComplianceItemDescription': f'Test compliance item {i+1}',
                    'ComplianceType': 'Control',
                    'IsRisk': random.choice([True, False]),
                    'ActiveInactive': 'Active',
                    'ComplianceVersion': '1.0',
                    'Status': 'Approved',
                    'CreatedByName': 'System',
                    'CreatedByDate': timezone.now().date()
                }
            )
            test_compliances.append(compliance)
        
        # Generate sample audits with varying completion times
        sample_audits = []
        for i in range(20):
            # Random completion time between 1 and 30 days
            completion_days = random.randint(1, 30)
            assigned_date = timezone.now() - timedelta(days=random.randint(30, 60))
            completion_date = assigned_date + timedelta(days=completion_days)
            
            audit = Audit.objects.create(
                Title=f'Sample Audit {i+1}',
                Scope=f'Test scope for audit {i+1}',
                Objective=f'Test objective for audit {i+1}',
                BusinessUnit='Test Unit',
                Role='Auditor',
                Responsibility='Conduct audit',
                Assignee=test_user,
                Auditor=test_user,
                Reviewer=test_user,
                FrameworkId=test_framework,
                PolicyId=test_policy,
                SubPolicyId=test_subpolicy,
                DueDate=assigned_date.date() + timedelta(days=30),
                Frequency=12,
                Status='Completed',
                CompletionDate=completion_date,
                ReviewStatus='Approved',
                AuditType='1',
                AssignedDate=assigned_date,
                ReviewDate=completion_date
            )
            sample_audits.append(audit)
        
        # Generate sample audit findings with evidence
        for audit in sample_audits:
            for compliance in test_compliances:
                # Randomly decide if evidence is provided
                has_evidence = random.choice([True, False])
                evidence_text = f'Sample evidence for audit {audit.AuditId} and compliance {compliance.ComplianceId}' if has_evidence else ''
                
                AuditFinding.objects.create(
                    AuditId=audit,
                    ComplianceId=compliance,
                    UserId=test_user,
                    Evidence=evidence_text,
                    Check='2',  # Completed
                    MajorMinor=random.choice(['0', '1']),  # Minor or Major
                    AssignedDate=audit.AssignedDate,
                    FrameworkId=audit.FrameworkId  # Auto-inject framework from parent audit
                )
        
        return Response({
            'success': True,
            'message': f'Generated {len(sample_audits)} sample audits with findings',
            'data': {
                'audits_created': len(sample_audits),
                'findings_created': len(sample_audits) * len(test_compliances),
                'test_user_id': test_user.UserId,
                'test_framework_id': test_framework.FrameworkId,
                'test_policy_id': test_policy.PolicyId
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating sample audit data: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)