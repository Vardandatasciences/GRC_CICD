"""
AI Document Relevance Analysis for Smart Compliance Mapping
Real AI-powered analysis using document content and compliance requirements
"""

import os
import json
import logging
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.db import connection
from ...rbac.decorators import audit_conduct_required
from ...rbac.permissions import AuditConductPermission
from .ai_audit_api import extract_text_from_document

logger = logging.getLogger(__name__)

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def analyze_document_relevance(request, audit_id):
    """
    Analyze document relevance to compliance requirements using real AI
    """
    try:
        logger.info(f"🤖 Starting AI document relevance analysis for audit: {audit_id}")
        
        # Get request data
        document_id = request.data.get('document_id')
        document_name = request.data.get('document_name')
        compliance_requirements = request.data.get('compliance_requirements', [])
        
        logger.info(f"📄 Document: {document_name} (ID: {document_id})")
        logger.info(f"📋 Compliance requirements: {len(compliance_requirements)}")
        
        if not document_id or not compliance_requirements:
            return Response({
                'success': False,
                'error': 'Document ID and compliance requirements are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get document from database using raw SQL
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT document_id, document_name, document_path, document_type, mime_type, file_size
                    FROM audit_document 
                    WHERE document_id = %s AND audit_id = %s
                """, [int(document_id), int(audit_id) if str(audit_id).isdigit() else audit_id])
                
                row = cursor.fetchone()
                
            if not row:
                logger.error(f"❌ Document not found: {document_id}")
                return Response({
                    'success': False,
                    'error': 'Document not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            doc_id, doc_name, file_path, doc_type, mime_type, file_size = row
            logger.info(f"✅ Found document in database: {doc_name}")
            
        except Exception as e:
            logger.error(f"❌ Database error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Database error retrieving document'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Extract document text
        if not os.path.isabs(file_path):
            file_path = os.path.join(settings.MEDIA_ROOT, file_path)
        
        logger.info(f"📖 Extracting text from: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"❌ File not found: {file_path}")
            return Response({
                'success': False,
                'error': 'Document file not found on server'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Extract text content - use mime_type for better accuracy
        document_text = extract_text_from_document(file_path, mime_type or doc_type)
        
        if not document_text or len(document_text.strip()) < 10:
            logger.error(f"❌ Unable to extract text from document: {document_name}")
            return Response({
                'success': False,
                'error': 'Unable to extract text from document'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"✅ Extracted {len(document_text)} characters from document")
        
        # Analyze relevance using AI in manageable batches to avoid oversized prompts
        def chunk_list(items, chunk_size):
            for i in range(0, len(items), chunk_size):
                yield items[i:i + chunk_size]

        combined_relevance_scores = {}
        combined_suggestions = []

        # Use a conservative chunk size to keep prompt + response within model limits
        CHUNK_SIZE = 10

        for batch in chunk_list(compliance_requirements, CHUNK_SIZE):
            relevance_analysis = analyze_relevance_with_ai(
                document_text=document_text,
                document_name=document_name,
                compliance_requirements=batch
            )

            if not relevance_analysis['success']:
                return Response({
                    'success': False,
                    'error': relevance_analysis['error']
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Merge batch results
            combined_relevance_scores.update(relevance_analysis['relevance_scores'])
            combined_suggestions.extend(relevance_analysis['suggested_compliances'])

        # De-duplicate suggestions by compliance_id keeping highest score
        best_by_id = {}
        for s in combined_suggestions:
            cid = s.get('compliance_id')
            prev = best_by_id.get(cid)
            if not prev or s.get('relevance_score', 0) > prev.get('relevance_score', 0):
                best_by_id[cid] = s

        # Sort final suggestions
        final_suggestions = sorted(best_by_id.values(), key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Format response
        response_data = {
            'success': True,
            'document_id': document_id,
            'document_name': document_name,
            'relevance_scores': combined_relevance_scores,
            'suggested_compliances': final_suggestions,
            'analysis_method': 'AI-powered',
            'total_compliances_analyzed': len(compliance_requirements)
        }
        
        logger.info(f"✅ AI relevance analysis complete for: {document_name}")
        logger.info(f"🎯 Found {len(final_suggestions)} relevant compliance requirements")
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"❌ Error in document relevance analysis: {str(e)}")
        return Response({
            'success': False,
            'error': f'Analysis failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def analyze_relevance_with_ai(document_text, document_name, compliance_requirements):
    """
    Use real AI (Ollama) to analyze document relevance to compliance requirements
    """
    try:
        logger.info("🤖 Using Ollama AI for document relevance analysis")
        
        # Prepare compliance requirements for AI analysis
        compliance_list = []
        for i, compliance in enumerate(compliance_requirements):
            compliance_list.append(f"{i+1}. {compliance.get('compliance_title', 'Unknown')} - {compliance.get('compliance_description', 'No description')}")
        
        compliance_text = "\n".join(compliance_list)
        
        # Create AI prompt for relevance analysis
        prompt = f"""You are an expert GRC auditor. Analyze this document and determine its relevance to each compliance requirement.

Document Name: {document_name}
Document Content: {document_text[:4000]}...

Compliance Requirements:
{compliance_text}

For each compliance requirement, analyze:
1. How relevant is this document to the requirement (0.0 to 1.0 score)?
2. What specific evidence or content makes it relevant?
3. What is missing that would make it more relevant?

Return ONLY valid JSON in this exact format:
{{
    "analysis_results": [
        {{
            "compliance_index": 1,
            "relevance_score": 0.85,
            "relevance_reason": "Document contains detailed access control procedures and user management policies",
            "evidence_found": ["user access procedures", "role-based permissions", "access review process"],
            "missing_elements": ["multi-factor authentication details"]
        }}
    ]
}}

Focus on content relevance, not just keyword matching. Score based on how well the document addresses the compliance requirement."""

        # Send to Ollama
        logger.info(f"🤖 Sending relevance analysis request to Ollama")
        # Try a couple of times in case the local model is busy spinning up
        last_exc = None
        for attempt in range(2):
            try:
                from django.conf import settings
                response = requests.post(f"{settings.OLLAMA_BASE_URL}/api/generate", 
                                       json={
                                           'model': getattr(settings, 'OLLAMA_MODEL', 'llama3.1'),
                                           'prompt': prompt,
                                           'format': 'json',
                                           'stream': False
                                       }, timeout=getattr(settings, 'OLLAMA_TIMEOUT', 60))
                break
            except requests.exceptions.Timeout as e:
                last_exc = e
                logger.warning("⏳ Ollama timeout, retrying once...")
                continue
        else:
            raise last_exc if last_exc else Exception("Unknown error calling Ollama")
        
        if response.status_code != 200:
            raise Exception(f"Ollama request failed: {response.status_code}. Make sure Ollama is running: ollama serve")
        
        # Handle different response formats from TinyLlama server
        try:
            json_response = response.json()
            ai_response = json_response.get('response', json_response.get('text', response.text))
        except:
            ai_response = response.text
        logger.info(f"🤖 AI Response length: {len(ai_response)} characters")
        
        # Parse AI response
        # Extract JSON from AI response
        start_idx = ai_response.find('{')
        end_idx = ai_response.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            raise Exception("No JSON found in AI response")
        
        json_str = ai_response[start_idx:end_idx]
        try:
            ai_analysis = json.loads(json_str)
        except Exception:
            # Import sanitizer from ai_audit_api if available
            try:
                from .ai_audit_api import _sanitize_and_parse_json
                ai_analysis = _sanitize_and_parse_json(json_str)
            except Exception:
                raise
            
            # Process AI results
            relevance_scores = {}
            suggested_compliances = []
            
            for result in ai_analysis.get('analysis_results', []):
                compliance_index = result.get('compliance_index', 0) - 1  # Convert to 0-based index
                
                if 0 <= compliance_index < len(compliance_requirements):
                    compliance = compliance_requirements[compliance_index]
                    compliance_id = compliance.get('compliance_id')
                    relevance_score = float(result.get('relevance_score', 0.0))
                    
                    relevance_scores[compliance_id] = relevance_score
                    
                    # Add to suggestions if score is high enough
                    if relevance_score >= 0.4:  # 40% threshold
                        suggested_compliances.append({
                            'compliance_id': compliance_id,
                            'compliance_title': compliance.get('compliance_title', 'Unknown'),
                            'relevance_score': relevance_score,
                            'relevance_reason': result.get('relevance_reason', 'AI analysis'),
                            'evidence_found': result.get('evidence_found', []),
                            'missing_elements': result.get('missing_elements', [])
                        })
            
            # Sort suggestions by relevance score
            suggested_compliances.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            logger.info(f"✅ AI analysis processed {len(relevance_scores)} compliance requirements")
            logger.info(f"🎯 Found {len(suggested_compliances)} relevant suggestions")
            
            return {
                'success': True,
                'relevance_scores': relevance_scores,
                'suggested_compliances': suggested_compliances
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse AI JSON response: {str(e)}")
            logger.error(f"❌ AI Response: {ai_response[:500]}...")
            raise Exception(f"AI returned invalid JSON: {str(e)}")
            
    except Exception as e:
        logger.error(f"❌ AI relevance analysis failed: {str(e)}")
        return {
            'success': False,
            'error': f'AI analysis failed: {str(e)}'
        }
