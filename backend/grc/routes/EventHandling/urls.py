from django.urls import path
from . import event_views, riskavaire_integration

urlpatterns = [
    # Event Management URLs
    path('events/frameworks/', event_views.get_frameworks_for_events, name='get-frameworks-for-events'),
    path('events/modules/', event_views.get_modules_for_events, name='get-modules-for-events'),
    path('events/event-types-by-framework/', event_views.get_event_types_by_framework, name='get-event-types-by-framework'),
    path('events/create-event-type/', event_views.create_event_type, name='create-event-type'),
    path('events/update-event-type-subtypes/<int:event_type_id>/', event_views.update_event_type_subtypes, name='update-event-type-subtypes'),
    path('events/records/', event_views.get_records_by_module, name='get-records-by-module'),
    path('events/templates/', event_views.get_event_templates, name='get-event-templates'),
    path('events/create/', event_views.create_event, name='create-event'),
    path('events/list/', event_views.get_events_list, name='get-events-list'),
    path('events/calendar/', event_views.get_events_for_calendar, name='get-events-for-calendar'),
    path('events/dashboard/', event_views.get_events_dashboard, name='get-events-dashboard'),
    path('events/permissions/', event_views.get_user_event_permissions, name='get-user-event-permissions'),
    path('events/<int:event_id>/approve/', event_views.approve_event, name='approve-event'),
    path('events/<int:event_id>/reject/', event_views.reject_event, name='reject-event'),
    path('events/<int:event_id>/update/', event_views.update_event, name='update-event'),
    path('events/<int:event_id>/archive/', event_views.archive_event, name='archive-event'),
    path('events/<int:event_id>/attach-evidence/', event_views.attach_evidence, name='attach-evidence'),
    path('events/<int:event_id>/', event_views.get_event_details, name='get-event-details'),
    path('events/archived/', event_views.get_archived_events, name='get-archived-events'),
    
    # Evidence linking URLs
    path('incidents/link-evidence/', event_views.link_evidence_to_incident, name='link-evidence-to-incident'),
    path('incidents/<int:incident_id>/linked-evidence/', event_views.get_incident_linked_evidence, name='get-incident-linked-evidence'),
    path('incidents/<int:incident_id>/linked-evidence/<str:evidence_id>/documents/<int:document_index>/download/', event_views.download_linked_evidence_document, name='download-linked-evidence-document'),
    
    # Database Schema URLs
    path('events/create-table/', event_views.create_events_table, name='create-events-table'),
    path('events/fix-schema/', event_views.fix_events_table_schema, name='fix-events-table-schema'),
    
    # RiskAvaire Integration URLs
    path('riskavaire/webhook/', riskavaire_integration.riskavaire_webhook, name='riskavaire-webhook'),
    path('riskavaire/check-triggers/', riskavaire_integration.check_automated_triggers, name='check-automated-triggers'),
    path('riskavaire/events/', riskavaire_integration.get_riskavaire_events, name='get-riskavaire-events'),
]
