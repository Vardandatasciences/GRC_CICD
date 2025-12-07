from django.db.models import Count, Avg, F, Q, Case, When, Value, FloatField
from django.db.models.functions import ExtractMonth, ExtractYear, Coalesce
from django.utils import timezone
from datetime import datetime, timedelta
from grc.models import Audit, AuditFinding, Compliance

def get_time_period_filter(time_filter, start_date=None, end_date=None):
    """Helper function to generate date range based on time filter"""
    now = timezone.now()
    
    if time_filter == 'week':
        start_date = now - timedelta(days=7)
        end_date = now
    elif time_filter == 'month':
        start_date = now - timedelta(days=30)
        end_date = now
    elif time_filter == 'quarter':
        start_date = now - timedelta(days=90)
        end_date = now
    elif time_filter == 'year':
        start_date = now - timedelta(days=365)
        end_date = now
    elif time_filter == 'custom' and start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        start_date = now - timedelta(days=30)  # Default to last 30 days
        end_date = now
    
    return start_date, end_date

def get_audit_completion_stats(time_filter, start_date=None, end_date=None):
    """Calculate audit completion statistics"""
    start_date, end_date = get_time_period_filter(time_filter, start_date, end_date)
    
    audits = Audit.objects.filter(assigned_date__range=[start_date, end_date])
    total_audits = audits.count()
    completed_audits = audits.filter(status='Completed').count()
    
    completion_ratio = (completed_audits / total_audits * 100) if total_audits > 0 else 0
    
    return {
        'total': total_audits,
        'completed': completed_audits,
        'ratio': round(completion_ratio, 2),
        'period_label': time_filter
    }

def get_audit_cycle_time(time_filter, start_date=None, end_date=None):
    """Calculate average audit cycle time"""
    start_date, end_date = get_time_period_filter(time_filter, start_date, end_date)
    
    avg_cycle_time = Audit.objects.filter(
        assigned_date__range=[start_date, end_date],
        completion_date__isnull=False
    ).annotate(
        cycle_days=F('completion_date') - F('assigned_date')
    ).aggregate(
        avg_days=Avg('cycle_days')
    )['avg_days']
    
    return {
        'average_cycle_time': round(avg_cycle_time.days if avg_cycle_time else 0, 2)
    }

def get_finding_rate(time_filter, start_date=None, end_date=None):
    """Calculate average findings per audit"""
    start_date, end_date = get_time_period_filter(time_filter, start_date, end_date)
    
    audits_with_findings = Audit.objects.filter(
        assigned_date__range=[start_date, end_date]
    ).annotate(
        finding_count=Count('auditfindings')
    )
    
    avg_findings = audits_with_findings.aggregate(
        avg=Avg('finding_count')
    )['avg']
    
    return {
        'average_findings': round(avg_findings if avg_findings else 0, 2)
    }

def get_time_to_close(time_filter, start_date=None, end_date=None):
    """Calculate average time to close findings"""
    start_date, end_date = get_time_period_filter(time_filter, start_date, end_date)
    
    findings = AuditFinding.objects.filter(
        assigned_date__range=[start_date, end_date],
        review_date__isnull=False
    ).annotate(
        close_days=F('review_date') - F('assigned_date')
    )
    
    avg_close_time = findings.aggregate(
        avg_days=Avg('close_days')
    )['avg_days']
    
    # Get top 5 oldest open findings
    oldest_open = AuditFinding.objects.filter(
        review_status__isnull=True
    ).annotate(
        days_open=timezone.now() - F('assigned_date')
    ).order_by('-days_open')[:5]
    
    return {
        'average_close_time': round(avg_close_time.days if avg_close_time else 0, 2),
        'oldest_open': [{
            'id': f.id,
            'audit_id': f.audit_id,
            'days_open': (timezone.now() - f.assigned_date).days
        } for f in oldest_open]
    }

def get_audit_pass_rate(time_filter, start_date=None, end_date=None):
    """Calculate audit pass rate"""
    start_date, end_date = get_time_period_filter(time_filter, start_date, end_date)
    
    audits = Audit.objects.filter(assigned_date__range=[start_date, end_date])
    total_audits = audits.count()
    passed_audits = audits.filter(status='Passed').count()
    
    pass_rate = (passed_audits / total_audits * 100) if total_audits > 0 else 0
    
    return {
        'pass_rate': round(pass_rate, 2),
        'total_audits': total_audits,
        'passed_audits': passed_audits
    }

def get_non_compliance_trend(time_filter, start_date=None, end_date=None):
    """Get trend of non-compliance issues"""
    start_date, end_date = get_time_period_filter(time_filter, start_date, end_date)
    
    findings = AuditFinding.objects.filter(
        assigned_date__range=[start_date, end_date]
    ).annotate(
        month=ExtractMonth('assigned_date'),
        year=ExtractYear('assigned_date')
    ).values('month', 'year').annotate(
        count=Count('id')
    ).order_by('year', 'month')
    
    trend_data = [{
        'period': f"{item['year']}-{item['month']:02d}",
        'count': item['count']
    } for item in findings]
    
    return {
        'trend_data': trend_data
    }

def get_severity_distribution(time_filter, start_date=None, end_date=None):
    """Get distribution of finding severities"""
    start_date, end_date = get_time_period_filter(time_filter, start_date, end_date)
    
    severity_counts = AuditFinding.objects.filter(
        assigned_date__range=[start_date, end_date]
    ).values('impact').annotate(
        count=Count('id')
    ).order_by('impact')
    
    return {
        'severity_distribution': [{
            'name': item['impact'],
            'value': item['count']
        } for item in severity_counts]
    }

def get_closure_rate(time_filter, start_date=None, end_date=None):
    """Calculate finding closure rate"""
    start_date, end_date = get_time_period_filter(time_filter, start_date, end_date)
    
    findings = AuditFinding.objects.filter(assigned_date__range=[start_date, end_date])
    total_findings = findings.count()
    closed_findings = findings.filter(review_status='Closed').count()
    
    closure_rate = (closed_findings / total_findings * 100) if total_findings > 0 else 0
    
    return {
        'closure_rate': round(closure_rate, 2),
        'total_findings': total_findings,
        'closed_findings': closed_findings
    }

def get_evidence_collection_progress(time_filter, start_date=None, end_date=None):
    """Calculate evidence collection progress"""
    start_date, end_date = get_time_period_filter(time_filter, start_date, end_date)
    
    audits = Audit.objects.filter(assigned_date__range=[start_date, end_date])
    total_required = audits.count()  # Assuming one evidence required per audit
    collected = audits.filter(evidence__isnull=False).count()
    
    collection_rate = (collected / total_required * 100) if total_required > 0 else 0
    
    return {
        'collection_rate': round(collection_rate, 2),
        'total_required': total_required,
        'collected': collected
    }

def get_compliance_readiness(time_filter, start_date=None, end_date=None):
    """Calculate overall compliance readiness"""
    start_date, end_date = get_time_period_filter(time_filter, start_date, end_date)
    
    total_controls = Compliance.objects.count()
    implemented_controls = Compliance.objects.filter(is_implemented=True).count()
    
    readiness_rate = (implemented_controls / total_controls * 100) if total_controls > 0 else 0
    
    return {
        'readiness_rate': round(readiness_rate, 2),
        'total_controls': total_controls,
        'implemented_controls': implemented_controls
    }

def get_report_timeliness(time_filter, start_date=None, end_date=None):
    """Calculate audit report timeliness"""
    start_date, end_date = get_time_period_filter(time_filter, start_date, end_date)
    
    audits = Audit.objects.filter(
        due_date__range=[start_date, end_date],
        completion_date__isnull=False
    ).annotate(
        days_difference=F('completion_date') - F('due_date')
    )
    
    total_reports = audits.count()
    on_time_reports = audits.filter(completion_date__lte=F('due_date')).count()
    avg_days_late = audits.aggregate(avg=Avg('days_difference'))['avg']
    
    on_time_percentage = (on_time_reports / total_reports * 100) if total_reports > 0 else 0
    
    return {
        'on_time_percentage': round(on_time_percentage, 2),
        'average_days_late': round(avg_days_late.days if avg_days_late else 0, 2),
        'total_reports': total_reports,
        'on_time_reports': on_time_reports
    } 