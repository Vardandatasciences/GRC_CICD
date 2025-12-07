from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
import sys
import os

# Add AI services to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ai_services', 'auditor_assignment'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ai_services', 'compliance'))

from .kpi_functions import (
    get_audit_completion_stats,
    get_audit_cycle_time,
    get_finding_rate,
    get_time_to_close,
    get_audit_pass_rate,
    get_non_compliance_trend,
    get_severity_distribution,
    get_closure_rate,
    get_evidence_collection_progress,
    get_compliance_readiness,
    get_report_timeliness
)

logger = logging.getLogger(__name__)

@api_view(['GET'])
def audit_completion(request):
    """Get audit completion statistics"""
    time_filter = request.GET.get('time_filter', 'month')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    data = get_audit_completion_stats(time_filter, start_date, end_date)
    return Response(data)

@api_view(['GET'])
def audit_cycle_time(request):
    """Get average audit cycle time"""
    time_filter = request.GET.get('time_filter', 'month')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    data = get_audit_cycle_time(time_filter, start_date, end_date)
    return Response(data)

@api_view(['GET'])
def finding_rate(request):
    """Get average findings per audit"""
    time_filter = request.GET.get('time_filter', 'month')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    data = get_finding_rate(time_filter, start_date, end_date)
    return Response(data)

@api_view(['GET'])
def time_to_close(request):
    """Get average time to close findings"""
    time_filter = request.GET.get('time_filter', 'month')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    data = get_time_to_close(time_filter, start_date, end_date)
    return Response(data)

@api_view(['GET'])
def audit_pass_rate(request):
    """Get audit pass rate"""
    time_filter = request.GET.get('time_filter', 'month')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    data = get_audit_pass_rate(time_filter, start_date, end_date)
    return Response(data)

@api_view(['GET'])
def non_compliance_trend(request):
    """Get non-compliance trend"""
    time_filter = request.GET.get('time_filter', 'month')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    data = get_non_compliance_trend(time_filter, start_date, end_date)
    return Response(data)

@api_view(['GET'])
def severity_distribution(request):
    """Get severity distribution of findings"""
    time_filter = request.GET.get('time_filter', 'month')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    data = get_severity_distribution(time_filter, start_date, end_date)
    return Response(data)

@api_view(['GET'])
def closure_rate(request):
    """Get finding closure rate"""
    time_filter = request.GET.get('time_filter', 'month')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    data = get_closure_rate(time_filter, start_date, end_date)
    return Response(data)

@api_view(['GET'])
def evidence_collection(request):
    """Get evidence collection progress"""
    time_filter = request.GET.get('time_filter', 'month')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    data = get_evidence_collection_progress(time_filter, start_date, end_date)
    return Response(data)

@api_view(['GET'])
def compliance_readiness(request):
    """Get compliance readiness status"""
    time_filter = request.GET.get('time_filter', 'month')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    data = get_compliance_readiness(time_filter, start_date, end_date)
    return Response(data)

# AI Recommendation Endpoints
@csrf_exempt
@require_http_methods(["POST"])
def get_ai_recommendations(request):
    """Get AI recommendations for auditors and reviewers"""
    try:
        # Parse request data
        data = json.loads(request.body)
        
        # Extract task data with additional context
        task_data = {
            'review_id': data.get('review_id'),
            'review_type': data.get('review_type', 'audit'),
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'domain': data.get('domain', 'General'),
            'severity': data.get('severity', 'Medium'),
            'department_id': data.get('department_id', 1),
            'objective': data.get('objective', ''),
            'responsibilities': data.get('responsibilities', ''),
            'page_context': data.get('pageContext', ''),
            'fieldType': data.get('fieldType', 'auditor'),  # Changed from field_type to fieldType
            'auditType': data.get('auditType', 'I'),  # Changed from audit_type to auditType
            'policy_context': data.get('policyContext', ''),
            'subpolicy_context': data.get('subpolicyContext', ''),
            'assigned_policy': data.get('assignedPolicy'),
            'assigned_subpolicy': data.get('assignedSubPolicy')
        }
        
        # Get max recommendations and field type
        max_recommendations = data.get('max_recommendations', 5)
        field_type = data.get('fieldType', 'auditor')  # 'auditor' or 'reviewer'
        
        # Initialize AI system
        from ai_services.auditor_assignment.advanced_recommendation_engine import AdvancedRecommendationEngine
        from ai_services.auditor_assignment.database.ai_database_service import AIDatabaseService
        
        db_service = AIDatabaseService()
        advanced_engine = AdvancedRecommendationEngine(db_service)
        
        # Get recommendations using AI/ML strategy
        result = advanced_engine.get_advanced_recommendations(
            task_data, 
            strategy='ai_ml',  # Use AI/ML strategy by default
            max_recommendations=max_recommendations
        )
        
        if result['success']:
            # Always return both auditor and reviewer recommendations
            recommendations = result['recommendations']
            print(f"🔍 API View - Field type: {field_type}")
            print(f"🔍 API View - Auditor recommendations: {len(recommendations.get('auditor_recommendations', []))}")
            print(f"🔍 API View - Reviewer recommendations: {len(recommendations.get('reviewer_recommendations', []))}")
            
            # Return both types of recommendations regardless of field type
            filtered_recommendations = {
                'auditor_recommendations': recommendations.get('auditor_recommendations', []),
                'reviewer_recommendations': recommendations.get('reviewer_recommendations', [])
            }
            
            print(f"🔍 API View - Final auditor recommendations: {len(filtered_recommendations.get('auditor_recommendations', []))}")
            print(f"🔍 API View - Final reviewer recommendations: {len(filtered_recommendations.get('reviewer_recommendations', []))}")
            
            return JsonResponse({
                'success': True,
                'data': {
                    'success': True,
                    'recommendations': filtered_recommendations,
                    'strategy_used': result.get('strategy_used'),
                    'timestamp': result.get('timestamp')
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Failed to get recommendations')
            }, status=500)
            
    except Exception as e:
        logger.error(f"AI Recommendation API Error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_ai_system_status(request):
    """Get AI system status and performance metrics"""
    try:
        from ai_services.auditor_assignment.advanced_recommendation_engine import AdvancedRecommendationEngine
        from ai_services.auditor_assignment.database.ai_database_service import AIDatabaseService
        
        db_service = AIDatabaseService()
        advanced_engine = AdvancedRecommendationEngine(db_service)
        
        # Get system status
        db_status = db_service.get_ai_system_status()
        analytics = advanced_engine.get_performance_analytics()
        
        return JsonResponse({
            'success': True,
            'database': db_status,
            'analytics': analytics
        })
        
    except Exception as e:
        logger.error(f"AI System Status Error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get system status'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def train_ai_models(request):
    """Train AI/ML models using historical audit data"""
    try:
        from ai_services.auditor_assignment.advanced_recommendation_engine import AdvancedRecommendationEngine
        from ai_services.auditor_assignment.database.ai_database_service import AIDatabaseService
        
        db_service = AIDatabaseService()
        advanced_engine = AdvancedRecommendationEngine(db_service)
        
        # Train ML models
        training_result = advanced_engine.train_ml_models()
        
        if training_result['success']:
            return JsonResponse({
                'success': True,
                'message': 'AI models trained successfully',
                'training_result': training_result
            })
        else:
            return JsonResponse({
                'success': False,
                'error': training_result.get('error', 'Training failed'),
                'training_result': training_result
            }, status=500)
        
    except Exception as e:
        logger.error(f"AI Model Training Error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Failed to train AI models: {str(e)}'
        }, status=500)

@api_view(['GET'])
def report_timeliness(request):
    """Get audit report timeliness metrics"""
    time_filter = request.GET.get('time_filter', 'month')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    data = get_report_timeliness(time_filter, start_date, end_date)
    return Response(data)

# AI Compliance Monitoring Views
@csrf_exempt
def analyze_compliance_with_ai(request):
    """AI-powered compliance status analysis"""
    try:
        # Parse JSON data
        import json
        data = json.loads(request.body)
        compliance_data = data.get('compliance_data', {})
        audit_evidence = data.get('audit_evidence', {})
        
        if not compliance_data:
            return JsonResponse({
                'success': False,
                'message': 'Compliance data is required'
            }, status=400)
        
        # Enhanced AI analysis with compliance framework recognition
        description = compliance_data.get('description', '').lower()
        requirements = compliance_data.get('requirements', '').lower()
        criticality = compliance_data.get('criticality', '').lower()
        evidence = audit_evidence.get('evidence', '').lower()
        
        # Detect compliance framework
        framework = 'General Compliance'
        if 'iso 27001' in requirements or 'iso27001' in requirements:
            framework = 'ISO 27001'
        elif 'nist' in requirements:
            framework = 'NIST'
        elif 'sox' in requirements or 'sarbanes' in requirements:
            framework = 'SOX'
        elif 'pci' in requirements or 'pci dss' in requirements:
            framework = 'PCI DSS'
        elif 'gdpr' in requirements:
            framework = 'GDPR'
        elif 'hipaa' in requirements:
            framework = 'HIPAA'
        
        # Analyze compliance status based on content
        compliance_score = 0
        status = 'Not Compliant'
        
        # Check for positive indicators
        positive_indicators = ['implemented', 'documented', 'reviewed', 'approved', 'tested', 'verified', 'compliant', 'secure']
        negative_indicators = ['missing', 'incomplete', 'failed', 'violation', 'breach', 'non-compliant', 'outdated']
        
        for indicator in positive_indicators:
            if indicator in description or indicator in evidence:
                compliance_score += 15
        
        for indicator in negative_indicators:
            if indicator in description or indicator in evidence:
                compliance_score -= 20
        
        # Determine status based on score
        if compliance_score >= 80:
            status = 'Fully Compliant'
        elif compliance_score >= 50:
            status = 'Partially Compliant'
        elif compliance_score >= 20:
            status = 'Non-Compliant'
        else:
            status = 'Critical Non-Compliant'
        
        # Calculate confidence based on evidence quality
        confidence = 60
        if evidence and len(evidence) > 50:
            confidence += 20
        if 'documented' in evidence or 'verified' in evidence:
            confidence += 15
        if 'tested' in evidence or 'audited' in evidence:
            confidence += 10
        
        # Determine risk level
        risk_level = 'Low'
        if criticality == 'high' or status in ['Non-Compliant', 'Critical Non-Compliant']:
            risk_level = 'High'
        elif criticality == 'medium' or status == 'Partially Compliant':
            risk_level = 'Medium'
        
        # Generate framework-specific recommendations
        recommendations = []
        if framework == 'ISO 27001':
            recommendations = [
                'Ensure information security policies are documented and approved',
                'Conduct regular risk assessments and security reviews',
                'Implement continuous monitoring and improvement processes'
            ]
        elif framework == 'NIST':
            recommendations = [
                'Follow NIST Cybersecurity Framework guidelines',
                'Implement proper access controls and monitoring',
                'Ensure incident response procedures are in place'
            ]
        elif framework == 'SOX':
            recommendations = [
                'Maintain proper financial controls and documentation',
                'Ensure audit trails are complete and accurate',
                'Implement proper segregation of duties'
            ]
        elif framework == 'PCI DSS':
            recommendations = [
                'Protect cardholder data with proper encryption',
                'Implement strong access control measures',
                'Regularly test security systems and processes'
            ]
        else:
            recommendations = [
                'Document all compliance activities and evidence',
                'Implement regular monitoring and review processes',
                'Ensure proper governance and oversight'
            ]
        
        ai_analysis = {
            'compliance_status': status,
            'confidence_score': min(confidence, 100),
            'risk_level': risk_level,
            'framework_detected': framework,
            'compliance_score': compliance_score,
            'ai_recommendations': recommendations,
            'analysis_details': {
                'text_analysis': f'Analyzed {framework} compliance requirements',
                'evidence_quality': 'Good' if evidence and len(evidence) > 50 else 'Needs Improvement',
                'compliance_trend': 'Improving' if compliance_score > 60 else 'Declining',
                'key_findings': [
                    f'Framework: {framework}',
                    f'Criticality: {criticality.title()}',
                    f'Evidence provided: {"Yes" if evidence else "No"}'
                ]
            }
        }
        
        return JsonResponse({
            'success': True,
            'ai_analysis': ai_analysis,
            'message': 'AI compliance analysis completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in AI compliance analysis: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error in AI compliance analysis: {str(e)}'
        }, status=500)

@csrf_exempt
def analyze_compliance_batch(request):
    """AI-powered batch compliance analysis for multiple items"""
    try:
        # Parse JSON data
        import json
        data = json.loads(request.body)
        compliance_items = data.get('compliance_items', [])
        analysis_type = data.get('analysis_type', 'batch_analysis')
        
        if not compliance_items:
            return JsonResponse({
                'success': False,
                'message': 'Compliance items are required'
            }, status=400)
        
        # Initialize Advanced AI Analyzer
        from ai_services.compliance.advanced_ai_analyzer import AdvancedAIAnalyzer
        ai_analyzer = AdvancedAIAnalyzer()
        
        # Analyze each compliance item using AI/ML
        item_analyses = []
        overall_scores = []
        overall_risks = []
        
        for item in compliance_items:
            # Prepare compliance data for AI analysis
            compliance_data = {
                'id': item.get('id', item.get('ComplianceId', 'unknown')),
                'title': item.get('Title', item.get('title', '')),
                'description': item.get('Description', item.get('description', '')),
                'requirement': item.get('Requirement', item.get('requirement', '')),
                'framework_name': item.get('FrameworkName', item.get('framework_name', '')),
                'category': item.get('Category', item.get('category', '')),
                'criticality': item.get('Criticality', item.get('criticality', 'Medium')),
                'audit_findings_status': item.get('audit_findings_status', 'Unknown')
            }
            
            # Perform AI analysis
            ai_analysis = ai_analyzer.analyze_compliance_item(compliance_data)
            
            # Create item analysis result
            item_analysis = {
                'id': compliance_data['id'],
                'title': compliance_data['title'] or compliance_data['description'][:50] + '...',
                'compliance_status': ai_analysis['compliance_status'],
                'compliance_score': ai_analysis['compliance_score'],
                'confidence_score': ai_analysis['confidence_score'],
                'risk_level': ai_analysis['risk_level'],
                'framework_detected': ai_analysis['framework_detected'],
                'current_status': compliance_data['audit_findings_status'],
                'ai_recommendations': ai_analysis['ai_recommendations'],
                'analysis_details': ai_analysis['analysis_details'],
                'ml_metrics': ai_analysis.get('ml_metrics', {})
            }
            
            item_analyses.append(item_analysis)
            overall_scores.append(ai_analysis['compliance_score'])
            overall_risks.append(ai_analysis['risk_level'])
        
        # Calculate overall analysis
        avg_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        
        if avg_score >= 80:
            overall_status = 'Fully Compliant'
        elif avg_score >= 50:
            overall_status = 'Partially Compliant'
        elif avg_score >= 20:
            overall_status = 'Non-Compliant'
        else:
            overall_status = 'Critical Non-Compliant'
        
        # Determine overall risk
        high_risk_count = overall_risks.count('High')
        if high_risk_count > len(overall_risks) / 2:
            overall_risk = 'High'
        elif high_risk_count > 0:
            overall_risk = 'Medium'
        else:
            overall_risk = 'Low'
        
        # Calculate overall confidence
        overall_confidence = min(95, 60 + (avg_score * 0.3))
        
        batch_analysis = {
            'overall_status': overall_status,
            'overall_confidence': round(overall_confidence, 1),
            'overall_risk': overall_risk,
            'average_score': round(avg_score, 1),
            'total_items': len(compliance_items),
            'item_analyses': item_analyses,
            'summary': {
                'fully_compliant': sum(1 for item in item_analyses if item['compliance_status'] == 'Fully Compliant'),
                'partially_compliant': sum(1 for item in item_analyses if item['compliance_status'] == 'Partially Compliant'),
                'non_compliant': sum(1 for item in item_analyses if item['compliance_status'] in ['Non-Compliant', 'Critical Non-Compliant']),
                'high_risk_items': sum(1 for item in item_analyses if item['risk_level'] == 'High')
            }
        }
        
        return JsonResponse({
            'success': True,
            'ai_analysis': batch_analysis,
            'message': f'AI batch analysis completed for {len(compliance_items)} items'
        })
        
    except Exception as e:
        logger.error(f"Error in AI batch compliance analysis: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error in AI batch compliance analysis: {str(e)}'
        }, status=500)

@csrf_exempt
def get_all_compliance_items(request):
    """Get all compliance items for AI analysis"""
    try:
        from django.db import connection
        
        # Get all compliance items with framework and policy information
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    c.ComplianceId as id,
                    c.ComplianceItemDescription as description,
                    c.ComplianceTitle as title,
                    c.ComplianceItemDescription as requirement,
                    c.Criticality as criticality,
                    c.MandatoryOptional as mandatory_optional,
                    c.Status as status,
                    c.ComplianceType as category,
                    f.FrameworkId as framework_id,
                    f.FrameworkName as framework_name,
                    p.PolicyId as policy_id,
                    p.PolicyName as policy_name,
                    sp.SubPolicyId as subpolicy_id,
                    sp.SubPolicyName as subpolicy_name,
                    af.`Check` as audit_findings_status,
                    af.Comments as comments,
                    af.Evidence as evidence
                FROM 
                    compliance c
                LEFT JOIN 
                    subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                LEFT JOIN 
                    policies p ON sp.PolicyId = p.PolicyId
                LEFT JOIN 
                    frameworks f ON p.FrameworkId = f.FrameworkId
                LEFT JOIN 
                    audit_findings af ON c.ComplianceId = af.ComplianceId
                WHERE 
                    c.Status IS NOT NULL
                ORDER BY 
                    f.FrameworkName, p.PolicyName, sp.SubPolicyName, c.ComplianceId
                LIMIT 100
            """)
            
            columns = [col[0] for col in cursor.description]
            compliance_items = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Process compliance items
        for item in compliance_items:
            # Convert audit findings status
            if item['audit_findings_status'] == '2':
                item['audit_findings_status'] = 'Fully Compliant'
            elif item['audit_findings_status'] == '1':
                item['audit_findings_status'] = 'Partially Compliant'
            elif item['audit_findings_status'] == '0':
                item['audit_findings_status'] = 'Not Compliant'
            else:
                item['audit_findings_status'] = 'Not Applicable'
            
            # Ensure all required fields have values
            item['description'] = item['description'] or item['title'] or 'No description available'
            item['title'] = item['title'] or item['description'][:50] + '...'
            item['framework_name'] = item['framework_name'] or 'General Compliance'
            item['category'] = item['category'] or 'General'
            
            # Create a proper title if missing
            if not item['title'] or item['title'] == 'None':
                item['title'] = item['description'][:50] + '...' if len(item['description']) > 50 else item['description']
        
        return JsonResponse({
            'success': True,
            'compliances': compliance_items,
            'total_count': len(compliance_items),
            'message': f'Loaded {len(compliance_items)} compliance items'
        })
        
    except Exception as e:
        logger.error(f"Error getting all compliance items: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error getting all compliance items: {str(e)}'
        }, status=500)

@csrf_exempt
def get_frameworks_for_ai(request):
    """Get frameworks for AI compliance analysis (no authentication required)"""
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    f.FrameworkId as id,
                    f.FrameworkName as name,
                    f.Category as category,
                    f.ActiveInactive as status,
                    f.FrameworkDescription as description
                FROM 
                    frameworks f
                WHERE 
                    f.ActiveInactive = 'Active'
                ORDER BY 
                    f.FrameworkName
            """)
            
            columns = [col[0] for col in cursor.description]
            frameworks = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return JsonResponse({
            'success': True,
            'frameworks': frameworks,
            'message': f'Loaded {len(frameworks)} frameworks'
        })
        
    except Exception as e:
        logger.error(f"Error getting frameworks for AI: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error getting frameworks: {str(e)}'
        }, status=500)

@csrf_exempt
def train_ai_models(request):
    """Train AI models on compliance data"""
    try:
        from ai_services.compliance.advanced_ai_analyzer import AdvancedAIAnalyzer
        from django.db import connection
        
        # Get training data from database
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    c.ComplianceId as id,
                    c.ComplianceItemDescription as description,
                    c.ComplianceTitle as title,
                    c.ComplianceItemDescription as requirement,
                    c.Criticality as criticality,
                    c.ComplianceType as category,
                    f.FrameworkName as framework_name,
                    af.`Check` as audit_findings_status
                FROM 
                    compliance c
                LEFT JOIN 
                    subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                LEFT JOIN 
                    policies p ON sp.PolicyId = p.PolicyId
                LEFT JOIN 
                    frameworks f ON p.FrameworkId = f.FrameworkId
                LEFT JOIN 
                    audit_findings af ON c.ComplianceId = af.ComplianceId
                WHERE 
                    c.Status IS NOT NULL
                LIMIT 500
            """)
            
            columns = [col[0] for col in cursor.description]
            training_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Process training data
        for item in training_data:
            # Convert audit findings status
            if item['audit_findings_status'] == '2':
                item['audit_findings_status'] = 'Fully Compliant'
            elif item['audit_findings_status'] == '1':
                item['audit_findings_status'] = 'Partially Compliant'
            elif item['audit_findings_status'] == '0':
                item['audit_findings_status'] = 'Not Compliant'
            else:
                item['audit_findings_status'] = 'Not Applicable'
            
            # Determine risk level based on criticality and status
            criticality = item.get('criticality', '').lower()
            status = item.get('audit_findings_status', '')
            
            if criticality == 'high' or status in ['Not Compliant', 'Critical Non-Compliant']:
                item['risk_level'] = 'High'
            elif criticality == 'medium' or status == 'Partially Compliant':
                item['risk_level'] = 'Medium'
            else:
                item['risk_level'] = 'Low'
        
        # Initialize AI analyzer and train models
        ai_analyzer = AdvancedAIAnalyzer()
        training_result = ai_analyzer.train_models(training_data)
        
        return JsonResponse({
            'success': True,
            'message': f'AI models trained on {len(training_data)} compliance items',
            'training_result': training_result
        })
        
    except Exception as e:
        logger.error(f"Error training AI models: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error training AI models: {str(e)}'
        }, status=500)

@csrf_exempt
def get_ai_compliance_dashboard(request):
    """Get AI-powered compliance dashboard data"""
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
        
        # Calculate AI insights
        total_compliances = sum(row['count'] for row in stats_result)
        compliant_count = sum(row['count'] for row in stats_result if row['status_code'] == '2')
        compliance_rate = (compliant_count / total_compliances * 100) if total_compliances > 0 else 0
        
        return JsonResponse({
            'success': True,
            'dashboard_data': {
                'compliance_statistics': stats_result,
                'compliance_rate': round(compliance_rate, 2),
                'total_compliances': total_compliances,
                'ai_insights': {
                    'overall_health': 'Good' if compliance_rate >= 80 else 'Needs Attention',
                    'risk_level': 'High' if compliance_rate < 60 else 'Medium' if compliance_rate < 80 else 'Low',
                    'recommendations': [
                        'Focus on high-criticality items' if compliance_rate < 80 else 'Maintain current compliance levels',
                        'Implement automated monitoring' if compliance_rate < 90 else 'Continue current practices'
                    ]
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting AI compliance dashboard: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error getting AI compliance dashboard: {str(e)}'
        }, status=500)

@api_view(['GET'])
def test_frameworks(request):
    """Test endpoint to get frameworks without authentication"""
    try:
        from grc.models import Framework
        
        frameworks = Framework.objects.all()[:5]  # Get first 5 frameworks
        
        frameworks_data = []
        for framework in frameworks:
            framework_data = {
                'id': framework.FrameworkId,
                'name': framework.FrameworkName,
                'category': framework.Category,
                'status': framework.ActiveInactive,
                'description': framework.FrameworkDescription,
                'versions': []
            }
            frameworks_data.append(framework_data)
        
        return Response({
            'success': True,
            'frameworks': frameworks_data,
            'message': 'Test frameworks loaded successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting test frameworks: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error getting test frameworks: {str(e)}'
        }, status=500) 