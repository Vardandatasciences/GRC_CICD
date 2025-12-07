"""
AI/ML Compliance Monitoring API Views
"""

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
import json

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def analyze_compliance_with_ai(request):
    """
    AI-powered compliance status analysis
    """
    try:
        # Get request data
        compliance_data = request.data.get('compliance_data', {})
        audit_evidence = request.data.get('audit_evidence', {})
        
        if not compliance_data:
            return Response({
                'success': False,
                'message': 'Compliance data is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize AI compliance monitor
        from ai_services.compliance.ai_compliance_monitor import AIComplianceMonitor
        from ai_services.auditor_assignment.database.ai_database_service import AIDatabaseService
        
        db_service = AIDatabaseService()
        ai_monitor = AIComplianceMonitor(db_service)
        
        # Analyze compliance status with AI
        ai_analysis = ai_monitor.analyze_compliance_status(compliance_data, audit_evidence)
        
        return Response({
            'success': True,
            'ai_analysis': ai_analysis,
            'message': 'AI compliance analysis completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in AI compliance analysis: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error in AI compliance analysis: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def predict_compliance_risk(request):
    """
    AI-powered compliance risk prediction
    """
    try:
        compliance_data = request.data.get('compliance_data', {})
        
        if not compliance_data:
            return Response({
                'success': False,
                'message': 'Compliance data is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize AI compliance monitor
        from ai_services.compliance.ai_compliance_monitor import AIComplianceMonitor
        from ai_services.auditor_assignment.database.ai_database_service import AIDatabaseService
        
        db_service = AIDatabaseService()
        ai_monitor = AIComplianceMonitor(db_service)
        
        # Create dummy evidence for prediction
        dummy_evidence = {
            'evidence': compliance_data.get('description', ''),
            'comments': '',
            'date': None
        }
        
        # Analyze with AI
        ai_analysis = ai_monitor.analyze_compliance_status(compliance_data, dummy_evidence)
        
        return Response({
            'success': True,
            'predicted_risk': ai_analysis['risk_level'],
            'confidence': ai_analysis['confidence_score'],
            'recommendations': ai_analysis['ai_recommendations']
        })
        
    except Exception as e:
        logger.error(f"Error in AI risk prediction: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error in AI risk prediction: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def real_time_compliance_check(request):
    """
    Real-time compliance status check using AI
    """
    try:
        # Get real-time data (e.g., security guard login/logout)
        event_type = request.data.get('event_type')  # 'login', 'logout', 'access_denied', etc.
        user_id = request.data.get('user_id')
        timestamp = request.data.get('timestamp')
        location = request.data.get('location')
        compliance_id = request.data.get('compliance_id')
        
        if not all([event_type, user_id, compliance_id]):
            return Response({
                'success': False,
                'message': 'event_type, user_id, and compliance_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get compliance data
        from ai_services.auditor_assignment.database.ai_database_service import AIDatabaseService
        db_service = AIDatabaseService()
        
        # Query compliance data
        compliance_query = """
        SELECT c.ComplianceId, c.ComplianceItemDescription, c.Criticality, c.ComplianceType
        FROM compliance c
        WHERE c.ComplianceId = %s
        """
        
        compliance_result = db_service.execute_query(compliance_query, (compliance_id,), fetch_results=True)
        
        if not compliance_result:
            return Response({
                'success': False,
                'message': 'Compliance not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        compliance_data = compliance_result[0]
        
        # Create evidence from real-time event
        audit_evidence = {
            'evidence': f"Real-time event: {event_type} by user {user_id} at {location} on {timestamp}",
            'comments': f"Automated compliance check for {event_type} event",
            'date': timestamp
        }
        
        # Initialize AI compliance monitor
        from ai_services.compliance.ai_compliance_monitor import AIComplianceMonitor
        ai_monitor = AIComplianceMonitor(db_service)
        
        # Analyze compliance status with AI
        ai_analysis = ai_monitor.analyze_compliance_status(compliance_data, audit_evidence)
        
        # Update compliance status in database
        status_code = {
            'Fully Compliant': '2',
            'Partially Compliant': '1', 
            'Not Compliant': '0',
            'Not Applicable': '3'
        }.get(ai_analysis['compliance_status'], '0')
        
        # Update audit finding
        update_query = """
        UPDATE audit_findings 
        SET Check = %s, Comments = %s, Evidence = %s
        WHERE ComplianceId = %s
        """
        
        db_service.execute_query(update_query, (
            status_code,
            f"AI Analysis: {ai_analysis['compliance_status']} (Confidence: {ai_analysis['confidence_score']}%)",
            audit_evidence['evidence'],
            compliance_id
        ))
        
        return Response({
            'success': True,
            'compliance_status': ai_analysis['compliance_status'],
            'confidence_score': ai_analysis['confidence_score'],
            'risk_level': ai_analysis['risk_level'],
            'ai_recommendations': ai_analysis['ai_recommendations'],
            'updated_database': True
        })
        
    except Exception as e:
        logger.error(f"Error in real-time compliance check: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error in real-time compliance check: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_ai_compliance_dashboard(request):
    """
    Get AI-powered compliance dashboard data
    """
    try:
        # Get compliance statistics with AI insights
        from ai_services.auditor_assignment.database.ai_database_service import AIDatabaseService
        db_service = AIDatabaseService()
        
        # Get compliance status counts
        stats_query = """
        SELECT 
            af.Check as status_code,
            COUNT(*) as count,
            CASE 
                WHEN af.Check = '2' THEN 'Fully Compliant'
                WHEN af.Check = '1' THEN 'Partially Compliant'
                WHEN af.Check = '0' THEN 'Not Compliant'
                WHEN af.Check = '3' THEN 'Not Applicable'
                ELSE 'Unknown'
            END as status_name
        FROM audit_findings af
        GROUP BY af.Check
        """
        
        stats_result = db_service.execute_query(stats_query, (), fetch_results=True)
        
        # Get high-risk compliances
        risk_query = """
        SELECT 
            c.ComplianceId,
            c.ComplianceItemDescription,
            c.Criticality,
            af.Check as status_code,
            af.Comments
        FROM compliance c
        JOIN audit_findings af ON c.ComplianceId = af.ComplianceId
        WHERE c.Criticality = 'High' AND af.Check IN ('0', '1')
        ORDER BY c.ComplianceId
        LIMIT 10
        """
        
        risk_result = db_service.execute_query(risk_query, (), fetch_results=True)
        
        # Calculate AI insights
        total_compliances = sum(row['count'] for row in stats_result)
        compliant_count = sum(row['count'] for row in stats_result if row['status_code'] == '2')
        compliance_rate = (compliant_count / total_compliances * 100) if total_compliances > 0 else 0
        
        return Response({
            'success': True,
            'dashboard_data': {
                'compliance_statistics': stats_result,
                'compliance_rate': round(compliance_rate, 2),
                'total_compliances': total_compliances,
                'high_risk_items': risk_result,
                'ai_insights': {
                    'overall_health': 'Good' if compliance_rate >= 80 else 'Needs Attention',
                    'risk_level': 'High' if len(risk_result) > 5 else 'Medium' if len(risk_result) > 2 else 'Low',
                    'recommendations': [
                        'Focus on high-criticality items' if len(risk_result) > 0 else 'Maintain current compliance levels',
                        'Implement automated monitoring' if compliance_rate < 90 else 'Continue current practices'
                    ]
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting AI compliance dashboard: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error getting AI compliance dashboard: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
