from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from ...models import Audit, AuditFinding, Framework
from datetime import datetime, timedelta
from calendar import monthrange
from django.db.models import Count, Q
from django.utils import timezone
from ...rbac.permissions import (
    AuditAnalyticsPermission, AuditViewAllPermission
)
from ...rbac.decorators import (
    audit_analytics_required, audit_view_all_required
)
from .framework_filter_helper import get_active_framework_filter, apply_framework_filter_to_audits

__all__ = [
    'get_audit_completion_rate',
    'get_total_audits',
    'get_open_audits',
    'get_completed_audits',
    'audit_completion_trend',
    'audit_compliance_trend',
    'audit_finding_trend',
    'framework_performance',
    'category_performance',
    'status_distribution',
    'recent_audit_activities',
    'category_distribution',
    'findings_distribution',
    'criticality_distribution',
    'department_performance',
    'compliance_trend'
]

@api_view(['GET'])
@permission_classes([AuditAnalyticsPermission])
@audit_analytics_required
def get_audit_completion_rate(request):
    # Get the current date
    today = datetime.today()

    # Get the first and last day of the current month
    first_day_current_month = today.replace(day=1)
    last_day_current_month = (first_day_current_month.replace(month=first_day_current_month.month % 12 + 1, year=first_day_current_month.year + first_day_current_month.month // 12) - timedelta(days=1))

    # Get the first and last day of the previous month
    first_day_previous_month = (first_day_current_month - timedelta(days=1)).replace(day=1)
    last_day_previous_month = first_day_current_month - timedelta(days=1)

    # Get filter parameters from query string
    framework_id = request.GET.get('framework_id')
    policy_id = request.GET.get('policy_id')
    
    # Start with all audits
    base_queryset = Audit.objects.all()
    
    # Apply framework filter if provided
    if framework_id and framework_id != 'all' and framework_id != '':
        base_queryset = base_queryset.filter(FrameworkId=framework_id)
    
    # Apply policy filter if provided
    if policy_id and policy_id != 'all' and policy_id != '':
        base_queryset = base_queryset.filter(PolicyId=policy_id)
    
    # Fallback to session-based filter if no query params
    if not framework_id and not policy_id:
        base_queryset = apply_framework_filter_to_audits(base_queryset, request)

    # Current month completion rate
    current_month_data = base_queryset.filter(AssignedDate__range=[first_day_current_month, last_day_current_month])
    planned_count_current = current_month_data.count()
    completed_count_current = current_month_data.filter(Status='Completed').count()
    current_month_rate = round((completed_count_current / planned_count_current * 100), 2) if planned_count_current else 0

    # Previous month completion rate
    previous_month_data = base_queryset.filter(AssignedDate__range=[first_day_previous_month, last_day_previous_month])
    planned_count_previous = previous_month_data.count()
    completed_count_previous = previous_month_data.filter(Status='Completed').count()
    previous_month_rate = round((completed_count_previous / planned_count_previous * 100), 2) if planned_count_previous else 0

    # Calculate the change in rate
    change_in_rate = round(current_month_rate - previous_month_rate, 2)

    return Response({
        'current_month_rate': current_month_rate,
        'previous_month_rate': previous_month_rate,
        'change_in_rate': change_in_rate,
        'is_positive_change': change_in_rate >= 0
    })

@api_view(['GET'])
@permission_classes([AuditAnalyticsPermission])
@audit_analytics_required
def get_total_audits(request):
    # Get filter parameters from query string
    framework_id = request.GET.get('framework_id')
    policy_id = request.GET.get('policy_id')
    
    # Start with ALL audits in database
    base_queryset = Audit.objects.all()
    
    # Apply framework filter if provided
    if framework_id and framework_id != 'all' and framework_id != '':
        base_queryset = base_queryset.filter(FrameworkId=framework_id)
    
    # Apply policy filter if provided
    if policy_id and policy_id != 'all' and policy_id != '':
        base_queryset = base_queryset.filter(PolicyId=policy_id)
    
    # Fallback to session-based filter if no query params
    if not framework_id and not policy_id:
        base_queryset = apply_framework_filter_to_audits(base_queryset, request)

    # Get total audits in database (NO TIME FILTER)
    total_audits = base_queryset.count()
    
    # Get audit status breakdown
    status_breakdown = base_queryset.values('Status').annotate(
        count=Count('AuditId')
    )
    
    # Get completed audits count
    completed_audits = base_queryset.filter(Status='Completed').count()
    
    # Get open audits count (not completed)
    open_audits = base_queryset.exclude(Status='Completed').count()

    print(f"\n{'='*60}")
    print(f"📊 [TOTAL AUDITS IN DATABASE]")
    print(f"{'='*60}")
    print(f"Framework ID: {framework_id}")
    print(f"Policy ID: {policy_id}")
    print(f"Total Audits Available: {total_audits}")
    print(f"Completed Audits: {completed_audits}")
    print(f"Open Audits (Not Completed): {open_audits}")
    print(f"\nStatus Breakdown:")
    for status in status_breakdown:
        print(f"  - {status['Status']}: {status['count']}")
    print(f"{'='*60}\n")

    return Response({
        'total_current_month': total_audits,
        'total_previous_month': 0,
        'change_in_total': total_audits,
        'is_positive_change': True,
        'total_audits': total_audits,
        'completed_audits': completed_audits,
        'open_audits': open_audits
    })

@api_view(['GET'])
@permission_classes([AuditAnalyticsPermission])
@audit_analytics_required
def get_open_audits(request):
    # Get filter parameters from query string
    framework_id = request.GET.get('framework_id')
    policy_id = request.GET.get('policy_id')
    
    # Start with ALL audits in database
    base_queryset = Audit.objects.all()
    
    # Apply framework filter if provided
    if framework_id and framework_id != 'all' and framework_id != '':
        base_queryset = base_queryset.filter(FrameworkId=framework_id)
    
    # Apply policy filter if provided
    if policy_id and policy_id != 'all' and policy_id != '':
        base_queryset = base_queryset.filter(PolicyId=policy_id)
    
    # Fallback to session-based filter if no query params
    if not framework_id and not policy_id:
        base_queryset = apply_framework_filter_to_audits(base_queryset, request)

    # Get ALL open audits (not completed) - NO TIME FILTER
    open_audits = base_queryset.exclude(Status='Completed').count()
    
    # Get detailed open audits information
    open_audits_details = base_queryset.exclude(Status='Completed').values('AuditId', 'Title', 'Status', 'AssignedDate', 'DueDate', 'FrameworkId')
    
    print(f"\n{'='*60}")
    print(f"📊 [OPEN AUDITS IN DATABASE]")
    print(f"{'='*60}")
    print(f"Framework ID: {framework_id}")
    print(f"Policy ID: {policy_id}")
    print(f"Total Open Audits: {open_audits}")
    print(f"\nOpen Audits Details:")
    for audit in open_audits_details:
        print(f"  - ID: {audit['AuditId']}, Title: {audit['Title']}, Status: {audit['Status']}, Assigned: {audit['AssignedDate']}")
    print(f"{'='*60}\n")

    return Response({
        'open_this_week': open_audits,
        'open_last_week': 0,
        'change_in_open': open_audits,
        'percent_change': 0,
        'is_improvement': False,
        'total_open_audits': open_audits
    })

@api_view(['GET'])
@permission_classes([AuditAnalyticsPermission])
@audit_analytics_required
def get_completed_audits(request):
    # Get filter parameters from query string
    framework_id = request.GET.get('framework_id')
    policy_id = request.GET.get('policy_id')
    
    # Start with ALL audits in database
    base_queryset = Audit.objects.all()
    
    # Apply framework filter if provided
    if framework_id and framework_id != 'all' and framework_id != '':
        base_queryset = base_queryset.filter(FrameworkId=framework_id)
    
    # Apply policy filter if provided
    if policy_id and policy_id != 'all' and policy_id != '':
        base_queryset = base_queryset.filter(PolicyId=policy_id)
    
    # Fallback to session-based filter if no query params
    if not framework_id and not policy_id:
        base_queryset = apply_framework_filter_to_audits(base_queryset, request)

    # Get ALL completed audits - NO TIME FILTER
    completed_audits = base_queryset.filter(Status='Completed').count()
    
    # Get detailed completed audits information
    completed_audits_details = base_queryset.filter(Status='Completed').values('AuditId', 'Title', 'Status', 'CompletionDate', 'AssignedDate')
    
    print(f"\n{'='*60}")
    print(f"📊 [COMPLETED AUDITS IN DATABASE]")
    print(f"{'='*60}")
    print(f"Framework ID: {framework_id}")
    print(f"Policy ID: {policy_id}")
    print(f"Total Completed Audits: {completed_audits}")
    print(f"\nCompleted Audits Details:")
    for audit in completed_audits_details:
        print(f"  - ID: {audit['AuditId']}, Title: {audit['Title']}, Completed: {audit['CompletionDate']}")
    print(f"{'='*60}\n")

    return Response({
        'this_week_count': completed_audits,
        'last_week_count': 0,
        'change_in_completed': completed_audits,
        'percent_change': 0,
        'is_improvement': True,
        'total_completed_audits': completed_audits
    })

@api_view(['GET'])
@permission_classes([AuditAnalyticsPermission])
@audit_analytics_required
def audit_completion_trend(request):
    current_year = datetime.today().year
    result = []

    # Get filter parameters from query string
    framework_id = request.GET.get('framework_id')
    policy_id = request.GET.get('policy_id')
    
    # Start with all audits
    base_queryset = Audit.objects.all()
    
    # Apply framework filter if provided
    if framework_id and framework_id != 'all' and framework_id != '':
        base_queryset = base_queryset.filter(FrameworkId=framework_id)
    
    # Apply policy filter if provided
    if policy_id and policy_id != 'all' and policy_id != '':
        base_queryset = base_queryset.filter(PolicyId=policy_id)
    
    # Fallback to session-based filter if no query params
    if not framework_id and not policy_id:
        base_queryset = apply_framework_filter_to_audits(base_queryset, request)

    # From January to current month (or you can set it as range(1, 13) for full year)
    for month in range(1, 8):  # Jan to July
        first_day = datetime(current_year, month, 1)
        last_day = datetime(current_year, month, monthrange(current_year, month)[1])

        audits = base_queryset.filter(AssignedDate__range=[first_day, last_day])
        total = audits.count()
        completed = audits.filter(Status='Completed').count()

        rate = round((completed / total) * 100, 2) if total else 0

        result.append({
            "month": first_day.strftime('%b'),  # Jan, Feb, ...
            "completion_rate": rate
        })

    return Response(result)

@api_view(['GET'])
@permission_classes([AuditAnalyticsPermission])
@audit_analytics_required
def audit_compliance_trend(request):
    current_year = datetime.today().year
    result = []

    # Get filter parameters from query string
    framework_id = request.GET.get('framework_id')
    policy_id = request.GET.get('policy_id')
    
    # Start with all audits
    base_queryset = Audit.objects.all()
    
    # Apply framework filter if provided
    if framework_id and framework_id != 'all' and framework_id != '':
        base_queryset = base_queryset.filter(FrameworkId=framework_id)
    
    # Apply policy filter if provided
    if policy_id and policy_id != 'all' and policy_id != '':
        base_queryset = base_queryset.filter(PolicyId=policy_id)
    
    # Fallback to session-based filter if no query params
    if not framework_id and not policy_id:
        base_queryset = apply_framework_filter_to_audits(base_queryset, request)
        
    filtered_audit_ids = list(base_queryset.values_list('AuditId', flat=True))

    # From January to current month
    for month in range(1, 8):  # Jan to July
        first_day = datetime(current_year, month, 1)
        last_day = datetime(current_year, month, monthrange(current_year, month)[1])

        # Get all audit findings for this month filtered by framework
        findings = AuditFinding.objects.filter(
            AssignedDate__range=[first_day, last_day],
            AuditId__in=filtered_audit_ids
        )
        total_findings = findings.count()
        
        # Using Impact field instead of ComplianceStatus since ComplianceStatus doesn't exist
        # Assuming findings with 'Low' Impact are considered compliant
        compliant_findings = findings.filter(Impact='Low').count()

        compliance_rate = round((compliant_findings / total_findings) * 100, 2) if total_findings else 0

        result.append({
            "month": first_day.strftime('%b'),  # Jan, Feb, ...
            "compliance_rate": compliance_rate
        })

    return Response(result)

@api_view(['GET'])
@permission_classes([AuditAnalyticsPermission])
@audit_analytics_required
def audit_finding_trend(request):
    current_year = datetime.today().year
    result = []

    # Get filter parameters from query string
    framework_id = request.GET.get('framework_id')
    policy_id = request.GET.get('policy_id')
    
    # Start with all audits
    base_queryset = Audit.objects.all()
    
    # Apply framework filter if provided
    if framework_id and framework_id != 'all' and framework_id != '':
        base_queryset = base_queryset.filter(FrameworkId=framework_id)
    
    # Apply policy filter if provided
    if policy_id and policy_id != 'all' and policy_id != '':
        base_queryset = base_queryset.filter(PolicyId=policy_id)
    
    # Fallback to session-based filter if no query params
    if not framework_id and not policy_id:
        base_queryset = apply_framework_filter_to_audits(base_queryset, request)
        
    filtered_audit_ids = list(base_queryset.values_list('AuditId', flat=True))

    # From January to current month
    for month in range(1, 8):  # Jan to July
        first_day = datetime(current_year, month, 1)
        last_day = datetime(current_year, month, monthrange(current_year, month)[1])

        # Get all findings for this month filtered by framework
        total_findings = AuditFinding.objects.filter(
            AssignedDate__range=[first_day, last_day],
            AuditId__in=filtered_audit_ids
        ).count()
        major_findings = AuditFinding.objects.filter(
            AssignedDate__range=[first_day, last_day], 
            Impact__in=['Critical', 'Major'],
            AuditId__in=filtered_audit_ids
        ).count()
        minor_findings = total_findings - major_findings

        result.append({
            "month": first_day.strftime('%b'),  # Jan, Feb, ...
            "total_findings": total_findings,
            "major_findings": major_findings,
            "minor_findings": minor_findings
        })

    return Response(result)

@api_view(['GET'])
@permission_classes([AuditAnalyticsPermission])
@audit_analytics_required
def framework_performance(request):
    # Get frameworks from the frameworks table instead of hardcoded values
    from django.db.models import Count, Q
    from ...models import Framework, Audit
    
    # Get filter parameters from query string (priority over session)
    framework_id = request.GET.get('framework_id')
    policy_id = request.GET.get('policy_id')
    
    # Fallback to session-based filter if no query params
    framework_id_filter = framework_id if (framework_id and framework_id != 'all') else get_active_framework_filter(request)
    
    # Fetch active frameworks from the database
    frameworks = Framework.objects.filter(ActiveInactive='Active')
    
    # If framework filter is active, only include that framework
    if framework_id_filter:
        frameworks = frameworks.filter(FrameworkId=framework_id_filter)
    
    frameworks = frameworks.values('FrameworkName', 'FrameworkId')
    
    # If no frameworks are found, try with different field names (database column might be different)
    if not frameworks.exists():
        try:
            # Try with different possible field names for active status
            frameworks = Framework.objects.all()
            if framework_id_filter:
                frameworks = frameworks.filter(FrameworkId=framework_id_filter)
            frameworks = frameworks.values('FrameworkName', 'FrameworkId')
        except Exception as e:
            # Log the error and return empty result
            print(f"Error fetching frameworks: {e}")
            return Response([])
    
    result = []

    for framework in frameworks:
        framework_id = framework['FrameworkId']
        framework_name = framework['FrameworkName']
        
        # Get audits for this framework - use FrameworkId_id instead of Framework
        audits = Audit.objects.filter(FrameworkId_id=framework_id)
        
        # Apply policy filter if provided
        if policy_id and policy_id != 'all' and policy_id != '':
            audits = audits.filter(PolicyId=policy_id)
            
        total = audits.count()
        
        if total > 0:
            # Count audits by status
            completed = audits.filter(Status='Completed').count()
            in_progress = audits.filter(Status='In Progress').count()
            yet_to_start = total - (completed + in_progress)
            
            # Calculate completion rate
            completion_rate = round((completed / total) * 100, 2)
            
            result.append({
                "framework": framework_name,
                "framework_id": framework_id,
                "completion_rate": completion_rate,
                "completed": completed,
                "in_progress": in_progress,
                "yet_to_start": yet_to_start
            })

    # Sort by framework name if there are results
    if result:
        result = sorted(result, key=lambda x: x['framework'])
        
    return Response(result)

@api_view(['GET'])
@permission_classes([AuditAnalyticsPermission])
@audit_analytics_required
def category_performance(request):
    # Get unique categories from the frameworks table
    from django.db.models import Count, Q
    from ...models import Framework, Audit
    
    # Get filter parameters from query string (priority over session)
    framework_id = request.GET.get('framework_id')
    policy_id = request.GET.get('policy_id')
    
    # Fallback to session-based filter if no query params
    framework_id_filter = framework_id if (framework_id and framework_id != 'all') else get_active_framework_filter(request)
    
    # Fetch distinct categories from frameworks
    try:
        # Get distinct categories from the Framework model
        frameworks_query = Framework.objects.all()
        if framework_id_filter:
            frameworks_query = frameworks_query.filter(FrameworkId=framework_id_filter)
        
        categories = frameworks_query.values_list('Category', flat=True).distinct()
        
        # If no categories found, use default categories
        if not categories:
            categories = ['Information Security', 'Data Protection', 'Risk Assessment', 'Access Control', 'Change Management']
    except Exception as e:
        # Log the error and use default categories
        print(f"Error fetching categories: {e}")
        categories = ['Information Security', 'Data Protection', 'Risk Assessment', 'Access Control', 'Change Management']
    
    result = []

    for category in categories:
        if not category:  # Skip empty categories
            continue
            
        # Get audits for this category through the framework
        framework_query = Framework.objects.filter(Category=category)
        if framework_id_filter:
            framework_query = framework_query.filter(FrameworkId=framework_id_filter)
        framework_ids = framework_query.values_list('FrameworkId', flat=True)
        
        # Use FrameworkId_id instead of Framework__in based on error message
        audits = Audit.objects.filter(FrameworkId_id__in=framework_ids)
        
        total = audits.count()
        completed = audits.filter(Status='Completed').count()
        
        # Calculate completion rate
        completion_rate = round((completed / total) * 100, 2) if total else 0
        
        result.append({
            "category": category,
            "completion_rate": completion_rate,
            "total": total,
            "completed": completed
        })
    
    # Sort by category name
    result = sorted(result, key=lambda x: x['category'])
    
    return Response(result)

@api_view(['GET'])
@permission_classes([AuditAnalyticsPermission])
@audit_analytics_required
def status_distribution(request):
    # Get filter parameters from query string
    framework_id = request.GET.get('framework_id')
    policy_id = request.GET.get('policy_id')
    
    # Start with all audits
    base_queryset = Audit.objects.all()
    
    # Apply framework filter if provided
    if framework_id and framework_id != 'all' and framework_id != '':
        base_queryset = base_queryset.filter(FrameworkId=framework_id)
    
    # Apply policy filter if provided
    if policy_id and policy_id != 'all' and policy_id != '':
        base_queryset = base_queryset.filter(PolicyId=policy_id)
    
    # Fallback to session-based filter if no query params
    if not framework_id and not policy_id:
        base_queryset = apply_framework_filter_to_audits(base_queryset, request)
    
    # Count audits by status
    total = base_queryset.count()
    completed = base_queryset.filter(Status='Completed').count()
    in_progress = base_queryset.filter(Status='In Progress').count()
    yet_to_start = total - (completed + in_progress)

    # Calculate percentages
    completed_percent = round((completed / total) * 100, 2) if total else 0
    in_progress_percent = round((in_progress / total) * 100, 2) if total else 0
    yet_to_start_percent = round((yet_to_start / total) * 100, 2) if total else 0

    return Response({
        "completed": completed,
        "in_progress": in_progress,
        "yet_to_start": yet_to_start,
        "completed_percent": completed_percent,
        "in_progress_percent": in_progress_percent,
        "yet_to_start_percent": yet_to_start_percent
    })

@api_view(['GET'])
@permission_classes([AuditViewAllPermission])
@audit_view_all_required
def recent_audit_activities(request):
    """
    Fetch recent audit activities including:
    - Recently completed audits
    - Recently received reviews
    - Audits with approaching due dates
    """
    try:
        from datetime import datetime, timedelta
        from django.db.models import F, Q
        from ...models import Audit, Framework
        from django.utils import timezone
        
        today = timezone.now()
        
        # Get filter parameters from query string
        framework_id = request.GET.get('framework_id')
        policy_id = request.GET.get('policy_id')
        
        # Start with all audits
        base_queryset = Audit.objects.all()
        
        # Apply framework filter if provided
        if framework_id and framework_id != 'all' and framework_id != '':
            base_queryset = base_queryset.filter(FrameworkId=framework_id)
        
        # Apply policy filter if provided
        if policy_id and policy_id != 'all' and policy_id != '':
            base_queryset = base_queryset.filter(PolicyId=policy_id)
        
        # Fallback to session-based filter if no query params
        if not framework_id and not policy_id:
            base_queryset = apply_framework_filter_to_audits(base_queryset, request)
        
        # Get audits completed in the last 7 days
        try:
            # Try with CompletionDate field first
            recent_completed = base_queryset.filter(
                Status='Completed',
                CompletionDate__isnull=False
            ).order_by('-CompletionDate')[:5]
            
            # If query returns no results, try alternative field names
            if not recent_completed.exists():
                print("No completed audits found with CompletionDate, trying alternative field names")
                # Try with alternative field name if it exists
                field_names = [f.name for f in Audit._meta.get_fields()]
                if 'CompletedDate' in field_names:
                    recent_completed = base_queryset.filter(
                        Status='Completed',
                        CompletedDate__isnull=False
                    ).order_by('-CompletedDate')[:5]
                elif 'completiondate' in field_names:
                    recent_completed = base_queryset.filter(
                        Status='Completed',
                        completiondate__isnull=False
                    ).order_by('-completiondate')[:5]
        except Exception as e:
            print(f"Error fetching completed audits: {e}")
            recent_completed = []
        
        # Get audits that received reviews in the last 7 days
        try:
            # Try with ReviewDate field first
            recent_reviews = base_queryset.filter(
                ReviewStatus__isnull=False,
                ReviewDate__isnull=False
            ).order_by('-ReviewDate')[:5]
            
            # If query returns no results, try alternative field names
            if not recent_reviews.exists():
                print("No reviewed audits found with ReviewDate, trying alternative field names")
                # Try with alternative field name if it exists
                field_names = [f.name for f in Audit._meta.get_fields()]
                if 'ReviewedDate' in field_names:
                    recent_reviews = base_queryset.filter(
                        ReviewStatus__isnull=False,
                        ReviewedDate__isnull=False
                    ).order_by('-ReviewedDate')[:5]
                elif 'reviewdate' in field_names:
                    recent_reviews = base_queryset.filter(
                        ReviewStatus__isnull=False,
                        reviewdate__isnull=False
                    ).order_by('-reviewdate')[:5]
        except Exception as e:
            print(f"Error fetching reviewed audits: {e}")
            recent_reviews = []
        
        # Get audits with due dates approaching in the next 7 days
        try:
            approaching_due = base_queryset.filter(
                Status__in=['In Progress', 'Not Started'],
                DueDate__isnull=False
            ).order_by('DueDate')[:5]
        except Exception as e:
            print(f"Error fetching approaching due audits: {e}")
            approaching_due = []
        
        # Prepare the result
        result = []
        
        # Add completed audits
        for audit in recent_completed:
            # Get framework name
            framework_name = "Unknown Framework"
            try:
                if audit.FrameworkId_id:
                    # Get only the necessary fields to avoid issues with unknown columns
                    framework = Framework.objects.filter(FrameworkId=audit.FrameworkId_id).values('FrameworkId', 'FrameworkName').first()
                    if framework and 'FrameworkName' in framework:
                        framework_name = framework['FrameworkName']
            except Exception as e:
                print(f"Error fetching framework: {e}")
            
            # Handle CompletionDate - ensure it's a string if it exists
            completion_date = None
            if audit.CompletionDate:
                try:
                    time_ago = get_time_ago(audit.CompletionDate)
                    completion_date = audit.CompletionDate.isoformat() if hasattr(audit.CompletionDate, 'isoformat') else str(audit.CompletionDate)
                except Exception as e:
                    print(f"Error formatting completion date: {e}")
                    time_ago = "Recently"
                    completion_date = None
            else:
                time_ago = "Recently"
            
            result.append({
                'type': 'completed',
                'audit_id': audit.AuditId,
                'title': 'Audit Completed',
                'description': f"{framework_name} - {audit.AuditType or 'Compliance Audit'}",
                'time_ago': time_ago,
                'timestamp': completion_date
            })
        
        # Add recently reviewed audits
        for audit in recent_reviews:
            # Get framework name
            framework_name = "Unknown Framework"
            try:
                if audit.FrameworkId_id:
                    # Get only the necessary fields to avoid issues with unknown columns
                    framework = Framework.objects.filter(FrameworkId=audit.FrameworkId_id).values('FrameworkId', 'FrameworkName').first()
                    if framework and 'FrameworkName' in framework:
                        framework_name = framework['FrameworkName']
            except Exception as e:
                print(f"Error fetching framework: {e}")
            
            # Handle ReviewDate
            review_date = None
            if audit.ReviewDate:
                try:
                    time_ago = get_time_ago(audit.ReviewDate)
                    review_date = audit.ReviewDate.isoformat() if hasattr(audit.ReviewDate, 'isoformat') else str(audit.ReviewDate)
                except Exception as e:
                    print(f"Error formatting review date: {e}")
                    time_ago = "Recently"
                    review_date = None
            else:
                time_ago = "Recently"
            
            result.append({
                'type': 'review',
                'audit_id': audit.AuditId,
                'title': 'Review Received',
                'description': f"{framework_name} {audit.AuditType or 'Compliance Audit'}",
                'time_ago': time_ago,
                'timestamp': review_date
            })
        
        # Add due dates approaching
        for audit in approaching_due:
            # Get framework name
            framework_name = "Unknown Framework"
            try:
                if audit.FrameworkId_id:
                    # Get only the necessary fields to avoid issues with unknown columns
                    framework = Framework.objects.filter(FrameworkId=audit.FrameworkId_id).values('FrameworkId', 'FrameworkName').first()
                    if framework and 'FrameworkName' in framework:
                        framework_name = framework['FrameworkName']
            except Exception as e:
                print(f"Error fetching framework: {e}")
            
            # Handle DueDate
            due_date = None
            if audit.DueDate:
                try:
                    time_ago = get_time_ago(audit.DueDate, future=True)
                    due_date = audit.DueDate.isoformat() if hasattr(audit.DueDate, 'isoformat') else str(audit.DueDate)
                except Exception as e:
                    print(f"Error formatting due date: {e}")
                    time_ago = "Soon"
                    due_date = None
            else:
                time_ago = "Soon"
            
            result.append({
                'type': 'due',
                'audit_id': audit.AuditId,
                'title': 'Due Date Approaching',
                'description': f"{framework_name} {audit.AuditType or 'Compliance Audit'}",
                'time_ago': time_ago,
                'timestamp': due_date
            })
        
        # Sort by timestamp (newest first)
        try:
            result.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        except Exception as e:
            print(f"Error sorting activities: {e}")
            # Don't sort if there's an error
        
        # Limit to 10 most recent activities
        result = result[:10]
        
        return Response(result)
    except Exception as e:
        print(f"Error in recent_audit_activities: {e}")
        # Return an empty list if there was an error
        return Response([])

def get_time_ago(date_time, future=False):
    """Helper function to format time difference in a human-readable format"""
    if not date_time:
        return ""
    
    # Make sure date_time is timezone-aware
    if timezone.is_naive(date_time):
        date_time = timezone.make_aware(date_time)
    
    now = timezone.now()
    
    try:
        if future:
            diff = date_time - now  # Time until the due date
        else:
            diff = now - date_time  # Time since the event
        
        days = diff.days
        seconds = diff.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if days > 30:
            months = days // 30
            return f"{months} {'month' if months == 1 else 'months'} {'until' if future else 'ago'}"
        elif days > 0:
            return f"{days} {'day' if days == 1 else 'days'} {'until' if future else 'ago'}"
        elif hours > 0:
            return f"{hours} {'hour' if hours == 1 else 'hours'} {'until' if future else 'ago'}"
        elif minutes > 0:
            return f"{minutes} {'minute' if minutes == 1 else 'minutes'} {'until' if future else 'ago'}"
        else:
            return "Just now"
    except Exception as e:
        print(f"Error calculating time difference: {e}")
        return "Recently" if not future else "Soon"

@api_view(['GET'])
@permission_classes([AuditAnalyticsPermission])
@audit_analytics_required
def category_distribution(request):
    """
    Get category distribution data for line chart
    Returns completion rates by category over time
    """
    try:
        from django.db.models import Count, Q
        from ...models import Framework, Audit
        
        # Get filter parameters from query string (priority over session)
        framework_id = request.GET.get('framework_id')
        policy_id = request.GET.get('policy_id')
        
        # Fallback to session-based filter if no query params
        framework_id_filter = framework_id if (framework_id and framework_id != 'all') else get_active_framework_filter(request)
        
        # Fetch distinct categories from frameworks
        try:
            frameworks_query = Framework.objects.all()
            if framework_id_filter:
                frameworks_query = frameworks_query.filter(FrameworkId=framework_id_filter)
            
            categories = frameworks_query.values_list('Category', flat=True).distinct()
            
            # If no categories found, use default categories
            if not categories:
                categories = ['Information Security', 'Data Protection', 'Risk Assessment', 'Access Control', 'Change Management']
        except Exception as e:
            print(f"Error fetching categories: {e}")
            categories = ['Information Security', 'Data Protection', 'Risk Assessment', 'Access Control', 'Change Management']
        
        result = []
        
        for category in categories:
            if not category:  # Skip empty categories
                continue
                
            # Get audits for this category through the framework
            framework_query = Framework.objects.filter(Category=category)
            if framework_id_filter:
                framework_query = framework_query.filter(FrameworkId=framework_id_filter)
            framework_ids = framework_query.values_list('FrameworkId', flat=True)
            
            # Use FrameworkId_id instead of Framework__in based on error message
            audits = Audit.objects.filter(FrameworkId_id__in=framework_ids)
            
            # Apply policy filter if provided
            if policy_id and policy_id != 'all' and policy_id != '':
                audits = audits.filter(PolicyId=policy_id)
            
            total = audits.count()
            completed = audits.filter(Status='Completed').count()
            
            # Calculate completion rate
            completion_rate = round((completed / total) * 100, 2) if total else 0
            
            result.append({
                "category": category,
                "completion_rate": completion_rate,
                "total": total,
                "completed": completed
            })
        
        # Sort by category name
        result = sorted(result, key=lambda x: x['category'])
        
        return Response(result)
    except Exception as e:
        print(f"Error in category_distribution: {e}")
        return Response([])

@api_view(['GET'])
@permission_classes([AuditAnalyticsPermission])
@audit_analytics_required
def findings_distribution(request):
    """
    Get findings distribution data for horizontal bar chart
    Returns findings count by severity level
    """
    try:
        from django.db.models import Count, Q
        from ...models import AuditFinding, Audit
        
        # Get filter parameters from query string
        framework_id = request.GET.get('framework_id')
        policy_id = request.GET.get('policy_id')
        
        # Start with all audits
        base_queryset = Audit.objects.all()
        
        # Apply framework filter if provided
        if framework_id and framework_id != 'all' and framework_id != '':
            base_queryset = base_queryset.filter(FrameworkId=framework_id)
        
        # Apply policy filter if provided
        if policy_id and policy_id != 'all' and policy_id != '':
            base_queryset = base_queryset.filter(PolicyId=policy_id)
        
        # Fallback to session-based filter if no query params
        if not framework_id and not policy_id:
            base_queryset = apply_framework_filter_to_audits(base_queryset, request)
            
        filtered_audit_ids = list(base_queryset.values_list('AuditId', flat=True))
        
        # Get findings for filtered audits
        findings = AuditFinding.objects.filter(AuditId__in=filtered_audit_ids)
        
        # Count findings by severity/impact level
        severity_counts = findings.values('Impact').annotate(count=Count('Impact'))
        
        # Define severity levels in order
        severity_levels = ['Critical', 'High', 'Medium', 'Low', 'Info']
        
        result = []
        for severity in severity_levels:
            count = 0
            for item in severity_counts:
                if item['Impact'] == severity:
                    count = item['count']
                    break
            
            result.append({
                "severity": severity,
                "count": count
            })
        
        return Response(result)
    except Exception as e:
        print(f"Error in findings_distribution: {e}")
        return Response([])

@api_view(['GET'])
@permission_classes([AuditAnalyticsPermission])
@audit_analytics_required
def criticality_distribution(request):
    """
    Get criticality distribution data for horizontal bar chart
    Returns findings count by Impact level (Critical, High, Medium, Low, Info)
    X-axis: Count, Y-axis: Criticality
    """
    try:
        from django.db.models import Count, Q
        from ...models import AuditFinding, Audit
        
        # Get filter parameters from query string
        framework_id = request.GET.get('framework_id')
        policy_id = request.GET.get('policy_id')
        
        # Start with all audits
        base_queryset = Audit.objects.all()
        
        # Apply framework filter if provided
        if framework_id and framework_id != 'all' and framework_id != '':
            base_queryset = base_queryset.filter(FrameworkId=framework_id)
        
        # Apply policy filter if provided
        if policy_id and policy_id != 'all' and policy_id != '':
            base_queryset = base_queryset.filter(PolicyId=policy_id)
        
        # Fallback to session-based filter if no query params
        if not framework_id and not policy_id:
            base_queryset = apply_framework_filter_to_audits(base_queryset, request)
            
        filtered_audit_ids = list(base_queryset.values_list('AuditId', flat=True))
        
        # Get findings for filtered audits
        findings = AuditFinding.objects.filter(AuditId__in=filtered_audit_ids)
        
        total_findings = findings.count()
        
        print(f"\n{'='*60}")
        print(f"📊 [CRITICALITY DISTRIBUTION] Chart")
        print(f"{'='*60}")
        print(f"Framework ID: {framework_id}")
        print(f"Policy ID: {policy_id}")
        print(f"Filtered Audit IDs: {len(filtered_audit_ids)}")
        print(f"Total Audits: {len(filtered_audit_ids)}")
        print(f"Total Findings: {total_findings}")
        
        # If no findings, return empty result
        if total_findings == 0:
            print(f"\n⚠️ No findings found for these audits!")
            print(f"{'='*60}\n")
            return Response([{
                "criticality": level,
                "count": 0
            } for level in ['Critical', 'High', 'Medium', 'Low', 'Info']])
        
        # Check MajorMinor field for criticality (this is the actual criticality field)
        print(f"\nFinding details - First 5 findings:")
        sample_findings = findings[:5]
        for f in sample_findings:
            print(f"  - Finding ID: {f.AuditFindingsId}, MajorMinor: '{f.MajorMinor}'")
        
        # Use MajorMinor field for criticality (Main field to use)
        majorminor_counts = findings.values('MajorMinor').annotate(count=Count('MajorMinor'))
        
        # Print MajorMinor counts
        all_majorminor = findings.values_list('MajorMinor', flat=True).distinct()
        print(f"\nMajorMinor values (this is the criticality field):")
        for mm in all_majorminor:
            count = findings.filter(MajorMinor=mm).count()
            print(f"  - MajorMinor='{mm}': {count} findings")
        
        # Define criticality levels in order (Y-axis)
        # Map database MajorMinor values to our criticality levels
        # MajorMinor: '1' = Major (Critical), '0' = Minor (Medium/Low), '2' = Not Applicable (Info)
        
        # Create a mapping dictionary for MajorMinor counts
        majorminor_dict = {}
        for item in majorminor_counts:
            mm_value = str(item['MajorMinor']).strip() if item['MajorMinor'] else ''
            majorminor_dict[mm_value] = item['count']
        
        print(f"\nMajorMinor Distribution:")
        print(f"  - Major ('1'): {majorminor_dict.get('1', 0)}")
        print(f"  - Minor ('0'): {majorminor_dict.get('0', 0)}")
        print(f"  - Not Applicable ('2'): {majorminor_dict.get('2', 0)}")
        
        # Map to 5 criticality levels
        major_count = majorminor_dict.get('1', 0)
        minor_count = majorminor_dict.get('0', 0)
        na_count = majorminor_dict.get('2', 0)
        
        # Distribute counts across levels
        result = [
            {"criticality": "Critical", "count": major_count},
            {"criticality": "High", "count": 0},
            {"criticality": "Medium", "count": minor_count},
            {"criticality": "Low", "count": 0},
            {"criticality": "Info", "count": na_count}
        ]
        
        print(f"\nCriticality Distribution Results (Mapped):")
        for item in result:
            print(f"  - {item['criticality']}: {item['count']}")
        print(f"{'='*60}\n")
        
        return Response(result)
    except Exception as e:
        print(f"Error in criticality_distribution: {e}")
        return Response([])

@api_view(['GET'])
@permission_classes([AuditAnalyticsPermission])
@audit_analytics_required
def department_performance(request):
    """
    Get department performance data for bar chart
    Returns audit scores by department
    """
    try:
        from django.db.models import Count, Q, Avg
        from ...models import Audit, Framework
        
        # Get filter parameters from query string
        framework_id = request.GET.get('framework_id')
        policy_id = request.GET.get('policy_id')
        
        # Start with all audits
        base_queryset = Audit.objects.all()
        
        # Apply framework filter if provided
        if framework_id and framework_id != 'all' and framework_id != '':
            base_queryset = base_queryset.filter(FrameworkId=framework_id)
        
        # Apply policy filter if provided
        if policy_id and policy_id != 'all' and policy_id != '':
            base_queryset = base_queryset.filter(PolicyId=policy_id)
        
        # Fallback to session-based filter if no query params
        if not framework_id and not policy_id:
            base_queryset = apply_framework_filter_to_audits(base_queryset, request)
        
        total_audits = base_queryset.count()
        
        print(f"\n{'='*60}")
        print(f"📊 [DEPARTMENT PERFORMANCE] Chart")
        print(f"{'='*60}")
        print(f"Framework ID: {framework_id}")
        print(f"Policy ID: {policy_id}")
        print(f"Total Audits (Filtered): {total_audits}")
        
        # Get audits with BusinessUnit information (Audit model has BusinessUnit field, not Department)
        try:
            # Try to get business unit data from Audit model
            audits_with_units = base_queryset.exclude(BusinessUnit__isnull=True).exclude(BusinessUnit='')
            
            print(f"Audits with Business Units: {audits_with_units.count()}")
            
            if audits_with_units.exists():
                # Group by BusinessUnit and calculate average completion rate
                unit_stats = audits_with_units.values('BusinessUnit').annotate(
                    total_audits=Count('AuditId'),
                    completed_audits=Count('AuditId', filter=Q(Status='Completed'))
                )
                
                result = []
                for unit in unit_stats:
                    unit_name = unit['BusinessUnit']
                    total = unit['total_audits']
                    completed = unit['completed_audits']
                    
                    # Calculate completion rate as score
                    completion_rate = round((completed / total) * 100, 2) if total else 0
                    
                    result.append({
                        "department": unit_name,
                        "score": completion_rate,
                        "total_audits": total,
                        "completed_audits": completed
                    })
                
                # Sort by department name
                result = sorted(result, key=lambda x: x['department'])
                
                print(f"\nDepartment Performance Results (Filtered):")
                for dept in result:
                    print(f"  - {dept['department']}: {dept['score']}% ({dept['completed_audits']}/{dept['total_audits']})")
                
            else:
                print(f"⚠️ No audits with business units found - returning empty result instead of mock data")
                # Fallback: return empty array to show no data when filtered
                result = []
                
        except Exception as e:
            print(f"Error fetching department data: {e}")
            print(f"{'='*60}\n")
            # Return empty array instead of mock data to respect filters
            result = []
        
        print(f"{'='*60}\n")
        return Response(result)
    except Exception as e:
        print(f"Error in department_performance: {e}")
        return Response([])

@api_view(['GET'])
@permission_classes([AuditAnalyticsPermission])
@audit_analytics_required
def compliance_trend(request):
    """
    Get compliance trend data for line chart
    Returns compliance rate over time (last 7 months)
    """
    try:
        from django.db.models import Count, Q
        from ...models import AuditFinding, Audit
        
        current_year = datetime.today().year
        current_month = datetime.today().month
        result = []
        
        # Get filter parameters from query string
        framework_id = request.GET.get('framework_id')
        policy_id = request.GET.get('policy_id')
        
        # Start with all audits
        base_queryset = Audit.objects.all()
        
        # Apply framework filter if provided
        if framework_id and framework_id != 'all' and framework_id != '':
            base_queryset = base_queryset.filter(FrameworkId=framework_id)
        
        # Apply policy filter if provided
        if policy_id and policy_id != 'all' and policy_id != '':
            base_queryset = base_queryset.filter(PolicyId=policy_id)
        
        # Fallback to session-based filter if no query params
        if not framework_id and not policy_id:
            base_queryset = apply_framework_filter_to_audits(base_queryset, request)
            
        filtered_audit_ids = list(base_queryset.values_list('AuditId', flat=True))
        
        # Get last 7 months of data
        for i in range(7):
            month = current_month - i
            year = current_year
            if month <= 0:
                month += 12
                year -= 1
            
            first_day = datetime(year, month, 1)
            last_day = datetime(year, month, monthrange(year, month)[1])
            
            # Get all audit findings for this month filtered by framework
            findings = AuditFinding.objects.filter(
                AssignedDate__range=[first_day, last_day],
                AuditId__in=filtered_audit_ids
            )
            total_findings = findings.count()
            
            # Using Impact field - assuming findings with 'Low' Impact are considered compliant
            compliant_findings = findings.filter(Impact='Low').count()
            
            compliance_rate = round((compliant_findings / total_findings) * 100, 2) if total_findings else 0
            
            result.append({
                "month": first_day.strftime('%b'),  # Jan, Feb, ...
                "compliance_rate": compliance_rate,
                "total_findings": total_findings,
                "compliant_findings": compliant_findings
            })
        
        # Reverse to get chronological order (oldest first)
        result.reverse()
        
        return Response(result)
    except Exception as e:
        print(f"Error in compliance_trend: {e}")
        return Response([])