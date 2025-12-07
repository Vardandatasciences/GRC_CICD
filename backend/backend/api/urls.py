from django.urls import path
from . import views

urlpatterns = [
    # KPI endpoints
    path('kpi/audit-completion/', views.audit_completion, name='audit-completion'),
    path('kpi/audit-cycle-time/', views.audit_cycle_time, name='audit-cycle-time'),
    path('kpi/finding-rate/', views.finding_rate, name='finding-rate'),
    path('kpi/time-to-close/', views.time_to_close, name='time-to-close'),
    path('kpi/audit-pass-rate/', views.audit_pass_rate, name='audit-pass-rate'),
    path('kpi/non-compliance-trend/', views.non_compliance_trend, name='non-compliance-trend'),
    path('kpi/severity-distribution/', views.severity_distribution, name='severity-distribution'),
    path('kpi/closure-rate/', views.closure_rate, name='closure-rate'),
    path('kpi/evidence-collection/', views.evidence_collection, name='evidence-collection'),
    path('kpi/compliance-readiness/', views.compliance_readiness, name='compliance-readiness'),
    path('kpi/report-timeliness/', views.report_timeliness, name='report-timeliness'),
    
    # AI Recommendation endpoints
    path('ai-recommendations/', views.get_ai_recommendations, name='ai-recommendations'),
    path('ai-system-status/', views.get_ai_system_status, name='ai-system-status'),
    path('train-ai-models/', views.train_ai_models, name='train-ai-models'),
    
    # AI Compliance Monitoring endpoints
    path('ai-compliance/analyze/', views.analyze_compliance_with_ai, name='analyze-compliance-with-ai'),
    path('ai-compliance/analyze-batch/', views.analyze_compliance_batch, name='analyze-compliance-batch'),
    path('ai-compliance/dashboard/', views.get_ai_compliance_dashboard, name='get-ai-compliance-dashboard'),
    
    # Compliance data endpoints
    path('ai-compliance/data/', views.get_all_compliance_items, name='get-all-compliance-items'),
    path('ai-compliance/frameworks/', views.get_frameworks_for_ai, name='get-frameworks-for-ai'),
    path('ai-compliance/train/', views.train_ai_models, name='train-ai-models'),
    
    # Test endpoints (no authentication required)
    path('test/frameworks/', views.test_frameworks, name='test-frameworks'),
] 