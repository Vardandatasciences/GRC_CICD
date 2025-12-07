"""
Compliance Mapping API
Provides endpoints for mapping documents to compliance requirements
"""

import logging
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

from ...models import Policy, SubPolicy, Compliance, AuditDocument
from ...routes.Global.logging_service import send_log
from ...rbac.permissions import (
    AuditViewPermission, AuditConductPermission, AuditReviewPermission,
    AuditAssignPermission, AuditAnalyticsPermission, AuditViewAllPermission
)
from ...rbac.decorators import (
    audit_assign_required,
    audit_conduct_required,
    audit_view_reports_required,
    audit_view_all_required,
    audit_review_required
)
from .framework_filter_helper import get_active_framework_filter, apply_framework_filter_to_audits, get_framework_sql_filter

# Import compliance mapping engine - REMOVED UNUSED IMPORT
# The ComplianceMappingEngine module doesn't exist, so we'll use rule-based mapping only
ComplianceMappingEngine = None
AI_AVAILABLE = False

logger = logging.getLogger(__name__)

# DRF Session auth variant that skips CSRF enforcement for API clients
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditConductPermission])
@audit_conduct_required
def map_document_to_compliance(request):
    """
    Map a document to compliance requirements
    """
    try:
        data = request.data
        document_text = data.get('document_text', '')
        document_type = data.get('document_type', 'document')
        policy_id = data.get('policy_id')
        subpolicy_id = data.get('subpolicy_id')
        document_id = data.get('document_id')
        
        if not document_text:
            return Response({
                'success': False,
                'error': 'Document text is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not policy_id:
            return Response({
                'success': False,
                'error': 'Policy ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify policy exists
        try:
            policy = Policy.objects.get(PolicyId=policy_id)
        except Policy.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Policy not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Use rule-based mapping (AI engine not available)
        mapping_result = get_rule_based_compliance_mapping(
            document_text, document_type, policy_id, subpolicy_id
        )
        
        # Log the mapping request
        send_log(
            module="Compliance_Mapping",
            actionType="DOCUMENT_MAPPED_TO_COMPLIANCE",
            description=f"Document mapped to compliance for policy {policy_id}",
            userId=request.session.get('user_id'),
            entityType="Policy",
            entityId=str(policy_id),
            additionalInfo={
                "policy_id": policy_id,
                "subpolicy_id": subpolicy_id,
                "document_type": document_type,
                "mappings_count": len(mapping_result.get('mappings', [])),
                "coverage_percentage": mapping_result.get('coverage_percentage', 0)
            }
        )
        
        return Response({
            'success': True,
            'policy_id': policy_id,
            'subpolicy_id': subpolicy_id,
            'document_type': document_type,
            'mapping_result': mapping_result,
            'ai_powered': AI_AVAILABLE
        })
        
    except Exception as e:
        logger.error(f"❌ Error mapping document to compliance: {e}")
        return Response({
            'success': False,
            'error': f'Error mapping document: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditConductPermission])
@audit_conduct_required
def get_policy_compliance_summary(request, policy_id):
    """
    Get compliance summary for a policy
    """
    try:
        # Verify policy exists
        try:
            policy = Policy.objects.get(PolicyId=policy_id)
        except Policy.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Policy not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Use basic summary (AI engine not available)
        summary = get_basic_compliance_summary(policy_id)
        
        return Response({
            'success': True,
            'policy_id': policy_id,
            'summary': summary,
            'ai_powered': AI_AVAILABLE
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting compliance summary: {e}")
        return Response({
            'success': False,
            'error': f'Error getting summary: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditConductPermission])
@audit_conduct_required
def map_audit_documents_to_compliance(request, audit_id):
    """
    Map all documents in an audit to compliance requirements
    """
    try:
        # Verify audit exists
        try:
            from ...models import Audit
            audit = Audit.objects.get(AuditId=audit_id)
        except Audit.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Audit not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all documents for the audit
        documents = AuditDocument.objects.filter(AuditId=audit_id)
        
        if not documents.exists():
            return Response({
                'success': False,
                'error': 'No documents found for this audit'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Prepare documents for mapping
        documents_data = []
        for doc in documents:
            # In a real implementation, you would extract text from the document
            # For now, we'll use a placeholder
            documents_data.append({
                'name': doc.DocumentName,
                'type': doc.DocumentType,
                'text': f"Document content for {doc.DocumentName}",  # Placeholder
                'policy_id': doc.PolicyId_id,
                'subpolicy_id': doc.SubPolicyId_id,
                'document_id': doc.DocumentId
            })
        
        # Use rule-based mapping (AI engine not available)
        mapping_result = get_rule_based_multiple_document_mapping(documents_data)
        
        # Log the mapping request
        send_log(
            module="Compliance_Mapping",
            actionType="AUDIT_DOCUMENTS_MAPPED_TO_COMPLIANCE",
            description=f"All audit documents mapped to compliance for audit {audit_id}",
            userId=request.session.get('user_id'),
            entityType="Audit",
            entityId=str(audit_id),
            additionalInfo={
                "audit_id": audit_id,
                "documents_count": len(documents_data),
                "overall_coverage": mapping_result.get('overall_coverage', 0),
                "overall_confidence": mapping_result.get('overall_confidence', 0)
            }
        )
        
        return Response({
            'success': True,
            'audit_id': audit_id,
            'mapping_result': mapping_result,
            'ai_powered': AI_AVAILABLE
        })
        
    except Exception as e:
        logger.error(f"❌ Error mapping audit documents: {e}")
        return Response({
            'success': False,
            'error': f'Error mapping documents: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditConductPermission])
@audit_conduct_required
def get_compliance_requirements(request, policy_id):
    """
    Get compliance requirements for a policy
    """
    try:
        # Verify policy exists
        try:
            policy = Policy.objects.get(PolicyId=policy_id)
        except Policy.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Policy not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get compliance requirements from database
        try:
            from ...models import Compliance
            compliances = Compliance.objects.filter(SubPolicy__PolicyId=policy_id)
            
            requirements = []
            for compliance in compliances:
                requirements.append({
                    'compliance_id': compliance.ComplianceId,
                    'compliance_title': compliance.ComplianceTitle,
                    'compliance_description': compliance.ComplianceItemDescription,
                    'compliance_type': compliance.ComplianceType,
                    'risk_level': compliance.Criticality,
                    'mandatory': compliance.MandatoryOptional == 'Mandatory',
                    'subpolicy_id': compliance.SubPolicy.SubPolicyId,
                    'subpolicy_name': compliance.SubPolicy.SubPolicyName
                })
            
            return Response({
                'success': True,
                'policy_id': policy_id,
                'policy_name': policy.PolicyName,
                'requirements': requirements,
                'total_requirements': len(requirements)
            })
            
        except Exception as e:
            logger.error(f"❌ Error getting compliance requirements: {e}")
            return Response({
                'success': False,
                'error': f'Error getting requirements: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        logger.error(f"❌ Error getting compliance requirements: {e}")
        return Response({
            'success': False,
            'error': f'Error getting requirements: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def get_rule_based_compliance_mapping(document_text: str, document_type: str, 
                                     policy_id: int, subpolicy_id: int = None) -> dict:
    """
    Fallback rule-based compliance mapping
    """
    try:
        # Basic keyword matching
        document_lower = document_text.lower()
        
        # Sample compliance requirements
        requirements = [
            {
                'compliance_id': 1,
                'compliance_title': 'Access Control Policy',
                'compliance_type': 'Security',
                'keywords': ['access', 'control', 'user', 'authentication', 'authorization'],
                'mandatory': True,
                'risk_level': 'High'
            },
            {
                'compliance_id': 2,
                'compliance_title': 'Data Encryption Standards',
                'compliance_type': 'Security',
                'keywords': ['encryption', 'data', 'protection', 'cipher', 'key'],
                'mandatory': True,
                'risk_level': 'High'
            }
        ]
        
        mappings = []
        for req in requirements:
            # Calculate keyword matches
            keyword_matches = sum(1 for keyword in req['keywords'] if keyword in document_lower)
            confidence = keyword_matches / len(req['keywords']) if req['keywords'] else 0
            
            if confidence > 0.3:
                mappings.append({
                    'compliance_id': req['compliance_id'],
                    'compliance_title': req['compliance_title'],
                    'compliance_type': req['compliance_type'],
                    'confidence': confidence,
                    'compliance_status': 'Compliant' if confidence > 0.7 else 'Needs Review',
                    'evidence_found': True,
                    'mandatory': req['mandatory'],
                    'risk_level': req['risk_level']
                })
        
        return {
            'mappings': mappings,
            'confidence': sum(m['confidence'] for m in mappings) / len(mappings) if mappings else 0,
            'coverage_percentage': len(mappings) / len(requirements) * 100,
            'missing_requirements': [req for req in requirements if not any(m['compliance_id'] == req['compliance_id'] for m in mappings)],
            'recommendations': ['Consider adding more specific compliance documentation'] if len(mappings) < 2 else []
        }
        
    except Exception as e:
        logger.error(f"❌ Error in rule-based mapping: {e}")
        return {
            'mappings': [],
            'confidence': 0.0,
            'coverage_percentage': 0.0,
            'missing_requirements': [],
            'recommendations': ['Error in compliance mapping']
        }

def get_basic_compliance_summary(policy_id: int) -> dict:
    """
    Basic compliance summary without AI
    """
    try:
        from ...models import Compliance
        compliances = Compliance.objects.filter(SubPolicy__PolicyId=policy_id)
        
        total_requirements = compliances.count()
        mandatory_requirements = compliances.filter(MandatoryOptional='Mandatory').count()
        
        risk_levels = {}
        compliance_types = {}
        
        for compliance in compliances:
            risk = compliance.Criticality or 'Medium'
            risk_levels[risk] = risk_levels.get(risk, 0) + 1
            
            comp_type = compliance.ComplianceType or 'General'
            compliance_types[comp_type] = compliance_types.get(comp_type, 0) + 1
        
        return {
            'policy_id': policy_id,
            'total_requirements': total_requirements,
            'mandatory_requirements': mandatory_requirements,
            'optional_requirements': total_requirements - mandatory_requirements,
            'risk_levels': risk_levels,
            'compliance_types': compliance_types
        }
        
    except Exception as e:
        logger.error(f"❌ Error in basic summary: {e}")
        return {'error': str(e)}

def get_rule_based_multiple_document_mapping(documents: list) -> dict:
    """
    Rule-based mapping for multiple documents
    """
    try:
        all_mappings = []
        total_coverage = 0
        total_confidence = 0
        
        for doc in documents:
            mapping = get_rule_based_compliance_mapping(
                doc.get('text', ''),
                doc.get('type', 'document'),
                doc.get('policy_id'),
                doc.get('subpolicy_id')
            )
            
            all_mappings.append({
                'document_name': doc.get('name', 'Unknown'),
                'document_type': doc.get('type', 'document'),
                'mapping': mapping
            })
            
            total_coverage += mapping.get('coverage_percentage', 0)
            total_confidence += mapping.get('confidence', 0)
        
        avg_coverage = total_coverage / len(documents) if documents else 0
        avg_confidence = total_confidence / len(documents) if documents else 0
        
        return {
            'documents': all_mappings,
            'overall_coverage': avg_coverage,
            'overall_confidence': avg_confidence,
            'total_documents': len(documents)
        }
        
    except Exception as e:
        logger.error(f"❌ Error in rule-based multiple mapping: {e}")
        return {'error': str(e)}
