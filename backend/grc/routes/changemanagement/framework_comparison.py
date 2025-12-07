"""
Framework Comparison API
Provides endpoints for comparing framework versions with amendments
"""

import os
import json
from datetime import datetime, timedelta
import uuid

from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from grc.models import Framework, Policy, SubPolicy, Compliance
from .similarity_matcher import get_similarity_matcher
from .framework_update_checker import run_framework_update_check
from .downloads_scanner import scan_downloads_folder, DownloadsScanner
import logging
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)


def _call_openai_for_compliance_matching(amendment_compliance: dict, db_compliances: list, framework_name: str) -> dict:
    """Use OpenAI to match an amendment compliance against database compliances"""
    try:
        import requests
        import json
        
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key or api_key == 'your-openai-api-key-here':
            raise Exception("OpenAI API key not configured")
        
        model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
        
        # Build prompt
        amendment_text = f"{amendment_compliance.get('compliance_title', '')}: {amendment_compliance.get('compliance_description', '')}"
        
        db_compliance_list = []
        for idx, db_comp in enumerate(db_compliances[:20], 1):  # Limit to 20 for token management
            db_compliance_list.append(f"{idx}. {db_comp['title']}: {db_comp['description']}")
        
        prompt = f"""You are an expert compliance auditor. Match the following NEW compliance requirement from a framework amendment against existing compliance requirements in the database.

FRAMEWORK: {framework_name}

NEW COMPLIANCE REQUIREMENT (from amendment):
{amendment_text}

EXISTING COMPLIANCE REQUIREMENTS (in database):
{chr(10).join(db_compliance_list)}

TASK:
Determine if the NEW compliance requirement matches any of the EXISTING requirements. Consider:
1. Semantic similarity (same concept, different wording)
2. Overlapping requirements (partial match)
3. Exact or near-exact matches

Return JSON with this structure:
{{
  "has_match": true/false,
  "best_match_index": <number or null>,
  "match_score": 0.0-1.0,
  "match_reason": "Brief explanation of match or why no match",
  "compliance_status": "COMPLIANT|PARTIALLY_COMPLIANT|NON_COMPLIANT",
  "recommendation": "Action recommendation"
}}

SCORING RULES:
- 0.9-1.0: Exact or near-exact match (COMPLIANT)
- 0.7-0.89: Strong semantic match (COMPLIANT)
- 0.5-0.69: Partial overlap (PARTIALLY_COMPLIANT)
- Below 0.5: No significant match (NON_COMPLIANT)

JSON:"""
        
        print(f"[ComplianceMatch][AI] Preparing OpenAI match for '{amendment_compliance.get('compliance_title', '')}' (framework: {framework_name})")

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': 'You are an expert GRC compliance auditor specializing in compliance requirement matching and gap analysis.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.1,
            'max_tokens': 500
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenAI API error {response.status_code}")
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Parse JSON from response
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            match_result = json.loads(json_match.group())
            print(
                "[ComplianceMatch][AI] Response parsed | "
                f"has_match={match_result.get('has_match')} | "
                f"score={match_result.get('match_score')} | "
                f"status={match_result.get('compliance_status')}"
            )
            
            # If there's a match, include the matched compliance details
            if match_result.get('has_match') and match_result.get('best_match_index'):
                idx = match_result['best_match_index'] - 1  # Convert to 0-based
                if 0 <= idx < len(db_compliances):
                    match_result['matched_compliance'] = db_compliances[idx]
            
            return match_result
        else:
            return {
                'has_match': False,
                'match_score': 0.0,
                'match_reason': 'Failed to parse AI response',
                'compliance_status': 'NON_COMPLIANT'
            }
        
    except Exception as e:
        logger.error(f"Error in AI compliance matching: {str(e)}")
        return {
            'has_match': False,
            'match_score': 0.0,
            'match_reason': f'Error: {str(e)}',
            'compliance_status': 'NON_COMPLIANT'
        }


def _extract_compliances_from_sections(sections: list) -> list:
    """Extract compliances from structured amendment sections"""
    compliances = []
    for section in sections or []:
        for policy in section.get('policies', []):
            policy_info = {
                'policy_identifier': policy.get('policy_identifier') or policy.get('policy_id') or policy.get('PolicyIdentifier'),
                'policy_name': policy.get('policy_title') or policy.get('policy_name') or policy.get('PolicyName'),
                'policy_description': policy.get('policy_description') or policy.get('PolicyDescription')
            }

            for subpolicy in policy.get('subpolicies', []):
                subpolicy_info = {
                    'subpolicy_identifier': subpolicy.get('subpolicy_identifier') or subpolicy.get('subpolicy_id') or subpolicy.get('SubPolicyIdentifier'),
                    'subpolicy_name': subpolicy.get('subpolicy_title') or subpolicy.get('subpolicy_name') or subpolicy.get('SubPolicyName'),
                    'subpolicy_description': subpolicy.get('subpolicy_description') or subpolicy.get('Description')
                }

                for compliance in subpolicy.get('compliance_records', []):
                    compliances.append({
                        'compliance_title': compliance.get('ComplianceTitle') or compliance.get('compliance_title') or compliance.get('title'),
                        'compliance_description': compliance.get('ComplianceItemDescription') or compliance.get('compliance_description') or compliance.get('description') or compliance.get('requirement'),
                        'compliance_type': compliance.get('ComplianceType') or compliance.get('compliance_type'),
                        'criticality': compliance.get('Criticality') or compliance.get('criticality'),
                        'policy_info': policy_info,
                        'subpolicy_info': subpolicy_info
                    })
    return compliances


def _match_compliances_with_ai(target_compliances: list, db_compliances: list, framework_name: str, use_ai: bool, threshold: float) -> dict:
    """Compare target compliances with database compliances using AI (fallback when ai_analysis is empty)"""
    results = {
        'matched': [],
        'unmatched': [],
        'total_target': len(target_compliances),
        'total_origin': len(db_compliances),
        'matched_count': 0,
        'unmatched_count': 0
    }

    if not target_compliances:
        return results

    for idx, target in enumerate(target_compliances, 1):
        logger.info(f"🔍 [AI Compliance Fallback] Matching structured compliance {idx}/{len(target_compliances)}")
        print(f"[ComplianceMatch][FallbackAI] Processing structured compliance {idx}/{len(target_compliances)} | title='{target.get('compliance_title', '')}' | use_ai={use_ai}")

        if use_ai:
            match_result = _call_openai_for_compliance_matching(target, db_compliances, framework_name)
            match_score = match_result.get('match_score', 0) or 0

            if match_result.get('has_match') and match_score >= threshold:
                results['matched'].append({
                    'target_compliance': target,
                    'matched_compliance': match_result.get('matched_compliance', {}),
                    'match_score': match_score,
                    'match_reason': match_result.get('match_reason'),
                    'compliance_status': match_result.get('compliance_status', 'COMPLIANT'),
                    'recommendation': match_result.get('recommendation')
                })
                results['matched_count'] += 1
            else:
                results['unmatched'].append({
                    'target_compliance': target,
                    'match_score': match_score,
                    'match_reason': match_result.get('match_reason', 'No matching compliance found'),
                    'compliance_status': match_result.get('compliance_status', 'NON_COMPLIANT'),
                    'message': 'We are not following this compliance'
                })
                results['unmatched_count'] += 1
        else:
            # Simple text similarity fallback
            best_match = None
            best_score = 0
            target_text = f"{target.get('compliance_title', '')} {target.get('compliance_description', '')}".lower()
            target_words = set(target_text.split())

            for db_comp in db_compliances:
                db_text = f"{db_comp.get('title', '')} {db_comp.get('description', '')}".lower()
                db_words = set(db_text.split())
                if target_words:
                    score = len(target_words & db_words) / len(target_words)
                    if score > best_score:
                        best_score = score
                        best_match = db_comp

            if best_match and best_score >= threshold:
                results['matched'].append({
                    'target_compliance': target,
                    'matched_compliance': best_match,
                    'match_score': best_score,
                    'match_reason': f'Text similarity: {best_score:.2%}',
                    'compliance_status': 'COMPLIANT' if best_score > 0.8 else 'PARTIALLY_COMPLIANT'
                })
                results['matched_count'] += 1
            else:
                results['unmatched'].append({
                    'target_compliance': target,
                    'match_score': best_score,
                    'match_reason': 'No matching compliance found',
                    'compliance_status': 'NON_COMPLIANT',
                    'message': 'We are not following this compliance'
                })
                results['unmatched_count'] += 1

    return results


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def add_compliance_from_amendment(request, framework_id):
    """
    Create Policy, SubPolicy, Compliance entries from amendment data (manual add)
    """
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        payload = request.data or {}

        policy_payload = payload.get('policy', {})
        subpolicy_payload = payload.get('subpolicy', {})
        compliance_payload = payload.get('compliance', {})

        if not compliance_payload.get('title') and not compliance_payload.get('description'):
            return Response({
                'success': False,
                'error': 'Compliance title or description is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = getattr(request, 'user', None)
        user_name = getattr(user, 'username', None) or getattr(user, 'UserName', None) or 'System'
        today = timezone.now().date()

        # Create Policy
        policy_identifier = policy_payload.get('identifier') or f"POL-{uuid.uuid4().hex[:8].upper()}"
        policy = Policy.objects.create(
            FrameworkId=framework,
            PolicyName=policy_payload.get('name') or compliance_payload.get('title') or 'Amendment Policy',
            PolicyDescription=policy_payload.get('description') or '',
            Identifier=policy_identifier,
            Status=policy_payload.get('status') or 'Draft',
            CurrentVersion=policy_payload.get('version') or '1.0',
            StartDate=policy_payload.get('start_date') or today,
            CreatedByName=user_name,
            CreatedByDate=today,
            Scope=policy_payload.get('scope', ''),
            Objective=policy_payload.get('objective', '')
        )

        # Create SubPolicy
        subpolicy_identifier = subpolicy_payload.get('identifier') or f"SUB-{uuid.uuid4().hex[:8].upper()}"
        subpolicy = SubPolicy.objects.create(
            PolicyId=policy,
            SubPolicyName=subpolicy_payload.get('name') or compliance_payload.get('title') or 'Amendment SubPolicy',
            Description=subpolicy_payload.get('description') or '',
            Identifier=subpolicy_identifier,
            Status=subpolicy_payload.get('status') or 'Draft',
            CreatedByName=user_name,
            CreatedByDate=today,
            Control=subpolicy_payload.get('control', ''),
            FrameworkId=framework
        )

        # Create Compliance
        compliance = Compliance.objects.create(
            SubPolicy=subpolicy,
            ComplianceTitle=compliance_payload.get('title') or 'New Compliance',
            ComplianceItemDescription=compliance_payload.get('description') or '',
            ComplianceType=compliance_payload.get('type') or '',
            Criticality=compliance_payload.get('criticality') or 'Medium',
            MandatoryOptional=compliance_payload.get('mandatory') or 'Mandatory',
            ManualAutomatic=compliance_payload.get('manual_automatic') or 'Manual',
            Status='Approved' if payload.get('auto_approve') else 'Under Review',
            ComplianceVersion='1.0',
            CreatedByName=user_name,
            CreatedByDate=today,
            FrameworkId=framework
        )

        response_data = {
            'success': True,
            'policy': {
                'PolicyId': policy.PolicyId,
                'PolicyName': policy.PolicyName,
                'Identifier': policy.Identifier
            },
            'subpolicy': {
                'SubPolicyId': subpolicy.SubPolicyId,
                'SubPolicyName': subpolicy.SubPolicyName,
                'Identifier': subpolicy.Identifier
            },
            'compliance': {
                'ComplianceId': compliance.ComplianceId,
                'ComplianceTitle': compliance.ComplianceTitle,
                'ComplianceItemDescription': compliance.ComplianceItemDescription
            }
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error adding compliance from amendment: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_frameworks_with_amendments(request):
    """
    Get all frameworks that have amendments
    Returns frameworks with non-empty Amendment column
    """
    try:
        # Get all frameworks (including those without amendments)
        frameworks = Framework.objects.values(
            'FrameworkId',
            'FrameworkName',
            'FrameworkDescription',
            'CurrentVersion',
            'Category',
            'Status',
            'Amendment'
        )
        
        # Add amendment count to each framework
        frameworks_list = []
        for fw in frameworks:
            fw_data = dict(fw)
            amendments = fw_data.get('Amendment') or []
            if not isinstance(amendments, list):
                amendments = []
            fw_data['amendment_count'] = len(amendments)
            fw_data['latest_amendment'] = amendments[-1] if amendments else None
            frameworks_list.append(fw_data)
        
        return Response({
            'success': True,
            'data': frameworks_list,
            'count': len(frameworks_list)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching frameworks with amendments: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def check_framework_updates(request, framework_id):
    """
    Trigger a Perplexity-based update check for a framework and update metadata.
    """
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        api_key = getattr(settings, 'PERPLEXITY_API_KEY', '')

        if not api_key:
            return Response({
                'success': False,
                'error': 'Perplexity API key is not configured on the server.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Prevent checks if a recent comparison already ran (<7 days)
        from datetime import date as date_type
        last_check_date = framework.latestComparisionCheckDate
        if isinstance(last_check_date, str):
            try:
                last_check_date = datetime.strptime(last_check_date, "%Y-%m-%d").date()
            except ValueError:
                last_check_date = None
        elif isinstance(last_check_date, datetime):
            last_check_date = last_check_date.date()
        elif isinstance(last_check_date, date_type):
            # Already a date object, no conversion needed
            pass
        else:
            last_check_date = None

        if last_check_date:
            today = timezone.now().date()
            days_since_check = (today - last_check_date).days
            
            # Allow multiple checks on the same day (days_since_check == 0)
            # Only enforce 7-day restriction starting from the next day
            # Block if last check was yesterday or earlier, but less than 7 days ago
            if days_since_check > 0 and days_since_check < 7:
                remaining_days = 7 - days_since_check
                return Response({
                    'success': False,
                    'warning': f'You already have the latest framework data. Please try again in {remaining_days} day(s).'
                }, status=status.HTTP_200_OK)
            # If days_since_check == 0 (same day), allow the check
            # If days_since_check >= 7, allow the check

        # Get last update date, handling various types (str, date, datetime)
        try:
            if framework.latestAmmendmentDate:
                if isinstance(framework.latestAmmendmentDate, str):
                    last_date_str = framework.latestAmmendmentDate
                elif isinstance(framework.latestAmmendmentDate, (datetime, date_type)):
                    last_date_str = framework.latestAmmendmentDate.strftime("%Y-%m-%d")
                else:
                    last_date_str = str(framework.latestAmmendmentDate)
            elif framework.latestComparisionCheckDate:
                if isinstance(framework.latestComparisionCheckDate, str):
                    last_date_str = framework.latestComparisionCheckDate
                elif isinstance(framework.latestComparisionCheckDate, (datetime, date_type)):
                    last_date_str = framework.latestComparisionCheckDate.strftime("%Y-%m-%d")
                else:
                    last_date_str = str(framework.latestComparisionCheckDate)
            elif framework.CreatedByDate:
                if isinstance(framework.CreatedByDate, str):
                    last_date_str = framework.CreatedByDate
                elif isinstance(framework.CreatedByDate, (datetime, date_type)):
                    last_date_str = framework.CreatedByDate.strftime("%Y-%m-%d")
                else:
                    last_date_str = str(framework.CreatedByDate)
            else:
                last_date_str = "1900-01-01"
        except Exception as e:
            logger.warning(f"Error parsing date fields: {str(e)}, using default date")
            last_date_str = "1900-01-01"

        # Documents will be stored in MEDIA_ROOT/change_management/
        # Clear the folder before checking for new updates
        download_dir = os.path.join(settings.MEDIA_ROOT, 'change_management')
        
        # Clear all files in change_management folder before starting
        if os.path.exists(download_dir):
            try:
                import shutil
                for filename in os.listdir(download_dir):
                    file_path = os.path.join(download_dir, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        logger.warning(f"Failed to delete {file_path}: {str(e)}")
                logger.info(f"Cleared change_management folder: {download_dir}")
            except Exception as e:
                logger.warning(f"Error clearing change_management folder: {str(e)}")
        
        os.makedirs(download_dir, exist_ok=True)

        # By default, do NOT auto-process - user will manually trigger via "Start Analysis"
        try:
            process_amendment = request.data.get('process_amendment', False) if hasattr(request, 'data') else False
        except Exception:
            process_amendment = False

        update_info = run_framework_update_check(
            framework_name=framework.FrameworkName,
            last_updated_date=last_date_str,
            api_key=api_key,
            download_dir=download_dir,
            framework_id=framework_id,
            process_amendment=process_amendment,
            store_in_media=True,
        )

        now = timezone.now().date()
        message = 'No new amendments found.'
        
        # Store document info temporarily - will be saved to DB only when Start Analysis is clicked
        downloaded_document_info = None

        if update_info.get('has_update') and update_info.get('latest_update_date'):
            try:
                latest_date = datetime.strptime(update_info['latest_update_date'], "%Y-%m-%d").date()
                
                # Check if document was downloaded
                downloaded_path = update_info.get('downloaded_path')
                processing_result = update_info.get('processing_result')
                document_url = update_info.get('document_url', 'N/A')
                
                if downloaded_path:
                    # Verify it's a PDF file (not a text file or other format)
                    is_pdf = downloaded_path.lower().endswith('.pdf') and os.path.exists(downloaded_path)
                    
                    if is_pdf:
                        # Get relative path for storing in database
                        relative_path = os.path.relpath(downloaded_path, settings.MEDIA_ROOT)
                        document_name = os.path.basename(downloaded_path)
                        
                        # Get S3 URL if available (preferred for viewing)
                        s3_url = update_info.get('s3_url')
                        s3_key = update_info.get('s3_key')
                        s3_stored_name = update_info.get('s3_stored_name')
                        
                        # Store document info temporarily (NOT saved to DB yet)
                        downloaded_document_info = {
                            'amendment_id': 1,
                            'amendment_name': f"{framework.FrameworkName} Amendment - {latest_date}",
                            'amendment_date': str(latest_date),
                            'document_path': downloaded_path,
                            'document_relative_path': relative_path,
                            'document_name': document_name,
                            'document_url': document_url,
                            's3_url': s3_url,  # S3 URL for viewing
                            's3_key': s3_key,
                            's3_stored_name': s3_stored_name,
                            'downloaded_date': datetime.now().isoformat(),
                            'processed': False,  # Mark as not processed yet
                            'extraction_summary': {},
                            'sections': [],
                            'framework_info': {},
                            'ai_analysis': {}
                        }
                        
                        # Store metadata in a JSON file alongside the PDF for later retrieval
                        metadata_file = os.path.join(os.path.dirname(downloaded_path), f"{os.path.splitext(document_name)[0]}_metadata.json")
                        try:
                            with open(metadata_file, 'w', encoding='utf-8') as f:
                                json.dump(downloaded_document_info, f, indent=2, ensure_ascii=False)
                            logger.info(f"Stored document metadata to: {metadata_file}")
                        except Exception as e:
                            logger.warning(f"Could not save metadata file: {str(e)}")
                        
                        message = f'New amendment detected and PDF downloaded. Please review the document and click "Start Analysis" to process and save it to the database.'
                        logger.info(f"Downloaded amendment document to: {downloaded_path}. Waiting for user to click 'Start Analysis' before saving to database.")
                    else:
                        # Not a valid PDF file
                        message = f'New amendment detected but PDF document is not available for download. Document URL: {document_url}. Please visit the URL to download manually.'
                        logger.warning(f"PDF document is not available for framework {framework_id}. document_url: {document_url}")
                else:
                    # Download failed or PDF not available
                    message = f'New amendment detected but PDF document is not available for download. Document URL: {document_url}. Please visit the URL to download manually.'
                    logger.warning(f"PDF document is not available for framework {framework_id}. document_url: {document_url}")
            except ValueError:
                message = 'Update detected but the provided date was invalid.'

        # Only update latestComparisionCheckDate (not latestAmmendmentDate or Amendment)
        # Amendment and latestAmmendmentDate will be updated only when Start Analysis is clicked
        framework.latestComparisionCheckDate = now
        framework.save(update_fields=['latestComparisionCheckDate'])
        
        # Return downloaded document info in response (NOT saved to DB yet)
        # Frontend will display it, and when user clicks "Start Analysis", we'll save to DB
        response_data = {
            'success': True,
            'message': message,
            'framework_id': framework.FrameworkId,
            'result': update_info
        }
        
        # Include downloaded document info if available (for frontend to display)
        if downloaded_document_info:
            response_data['downloaded_document'] = downloaded_document_info
            logger.info(f"Returning downloaded document info in response (not saved to DB yet)")

        return Response(response_data, status=status.HTTP_200_OK)

    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Error checking framework updates: {str(e)}\n{error_traceback}")
        return Response({
            'success': False,
            'error': str(e),
            'details': error_traceback if settings.DEBUG else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def scan_downloads_for_processing(request):
    """
    Scan the downloads folder and automatically process any PDF files found.
    
    This endpoint:
    1. Scans the downloads folder for PDF files
    2. Matches PDFs to frameworks by filename
    3. Processes each PDF (extracts policies, subpolicies, compliance)
    4. Stores results in Framework.Amendment field
    
    Request Body (optional):
    {
        "process_all": false  // If true, reprocess already processed files
    }
    
    Returns:
    {
        "success": true,
        "summary": {
            "total_files": 5,
            "processed": 3,
            "skipped": 1,
            "failed": 1
        },
        "processed": [...],
        "skipped": [...],
        "failed": [...]
    }
    """
    try:
        process_all = request.data.get('process_all', False)
        
        logger.info(f"Manual scan of downloads folder triggered (process_all={process_all})")
        
        # Scan and process downloads folder
        result = scan_downloads_folder(process_all=process_all)
        
        return Response({
            'success': result.get('success', True),
            'message': f"Scanned downloads folder: {result.get('summary', {}).get('processed', 0)} processed, {result.get('summary', {}).get('skipped', 0)} skipped, {result.get('summary', {}).get('failed', 0)} failed",
            'summary': result.get('summary', {}),
            'processed': result.get('processed', []),
            'skipped': result.get('skipped', []),
            'failed': result.get('failed', [])
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error scanning downloads folder: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_framework_amendments(request, framework_id):
    """
    Get all amendments for a specific framework
    """
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        amendments = framework.Amendment if framework.Amendment else []
        
        return Response({
            'success': True,
            'framework_id': framework.FrameworkId,
            'framework_name': framework.FrameworkName,
            'amendments': amendments,
            'count': len(amendments)
        }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching amendments for framework {framework_id}: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_framework_origin_data(request, framework_id):
    """
    Get origin (current) framework data with full hierarchy:
    Framework -> Policies -> SubPolicies -> Compliances
    """
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        
        # Get all policies for this framework
        policies = Policy.objects.filter(FrameworkId=framework_id).values(
            'PolicyId',
            'PolicyName',
            'PolicyDescription',
            'Identifier',
            'Status',
            'CurrentVersion'
        )
        
        policies_data = []
        db_compliances = []
        for policy in policies:
            # Get subpolicies for each policy
            subpolicies = SubPolicy.objects.filter(PolicyId=policy['PolicyId']).values(
                'SubPolicyId',
                'SubPolicyName',
                'Description',
                'Identifier',
                'Status'
            )
            
            subpolicies_data = []
            for subpolicy in subpolicies:
                # Get compliances for each subpolicy
                compliances = Compliance.objects.filter(SubPolicy=subpolicy['SubPolicyId']).values(
                    'ComplianceId',
                    'ComplianceTitle',
                    'ComplianceItemDescription',
                    'ComplianceType',
                    'Status',
                    'Criticality',
                    'MaturityLevel',
                    'ManualAutomatic',
                    'MandatoryOptional'
                )
                compliance_list = list(compliances)
                
                subpolicies_data.append({
                    **subpolicy,
                    'compliances': compliance_list
                })

                for comp in compliance_list:
                    db_compliances.append({
                        'compliance_id': comp.get('ComplianceId'),
                        'title': comp.get('ComplianceTitle') or '',
                        'description': comp.get('ComplianceItemDescription') or '',
                        'type': comp.get('ComplianceType'),
                        'criticality': comp.get('Criticality'),
                        'mandatory': (comp.get('MandatoryOptional') or '').lower() == 'mandatory',
                        'policy_name': policy.get('PolicyName'),
                        'policy_identifier': policy.get('Identifier'),
                        'subpolicy_name': subpolicy.get('SubPolicyName'),
                        'subpolicy_identifier': subpolicy.get('Identifier')
                    })
            
            policies_data.append({
                **policy,
                'subpolicies': subpolicies_data
            })
        
        return Response({
            'success': True,
            'framework': {
                'FrameworkId': framework.FrameworkId,
                'FrameworkName': framework.FrameworkName,
                'FrameworkDescription': framework.FrameworkDescription,
                'CurrentVersion': framework.CurrentVersion,
                'Status': framework.Status
            },
            'policies': policies_data,
            'total_policies': len(policies_data)
        }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching origin data for framework {framework_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_framework_target_data(request, framework_id, amendment_id=None):
    """
    Get target (amended) framework data from Amendment JSON
    If amendment_id is provided, get specific amendment
    Otherwise, get the latest amendment
    """
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        amendments = framework.Amendment if framework.Amendment else []
        
        if not amendments:
            return Response({
                'success': False,
                'framework': {
                    'FrameworkId': framework.FrameworkId,
                    'FrameworkName': framework.FrameworkName,
                },
                'message': 'No amendments found for this framework.'
            }, status=status.HTTP_200_OK)
        
        # Get specific amendment or latest
        if amendment_id is not None:
            try:
                amendment_idx = int(amendment_id) - 1
                if amendment_idx < 0 or amendment_idx >= len(amendments):
                    return Response({
                        'success': False,
                        'error': f'Amendment ID {amendment_id} not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                target_amendment = amendments[amendment_idx]
            except (ValueError, IndexError):
                return Response({
                    'success': False,
                    'error': f'Invalid amendment ID {amendment_id}'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            target_amendment = amendments[-1]  # Latest amendment
        
        # Extract amendment data
        ai_analysis = target_amendment.get('ai_analysis', {})
        modified_controls = ai_analysis.get('modified_controls', [])
        new_additions = ai_analysis.get('new_additions', [])
        framework_references = ai_analysis.get('framework_references', [])
        modified_sections = target_amendment.get('modified_sections', [])
        sections = target_amendment.get('sections', [])
        extraction_summary = target_amendment.get('extraction_summary', {})
        
        return Response({
            'success': True,
            'framework': {
                'FrameworkId': framework.FrameworkId,
                'FrameworkName': framework.FrameworkName,
            },
            'amendment': {
                'amendment_id': target_amendment.get('amendment_id'),
                'amendment_name': target_amendment.get('amendment_name'),
                'uploaded_date': target_amendment.get('uploaded_date'),
                's3_url': target_amendment.get('s3_url'),
                'content_summary': target_amendment.get('content_summary'),
            },
            'modified_controls': modified_controls,
            'new_additions': new_additions,
            'framework_references': framework_references,
            'modified_sections': modified_sections,
            'sections': sections,
            'extraction_summary': extraction_summary,
            'stats': {
                'total_modified': len(modified_controls),
                'total_new': len(new_additions),
                'total_references': len(framework_references),
                'total_structured_policies': extraction_summary.get('total_policies', 0),
                'total_structured_subpolicies': extraction_summary.get('total_subpolicies', 0),
                'total_structured_compliances': extraction_summary.get('total_compliance_records', 0)
            }
        }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching target data for framework {framework_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_framework_comparison_summary(request, framework_id):
    """
    Get summary statistics for framework comparison
    """
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        amendments = framework.Amendment if framework.Amendment else []
        
        if not amendments:
            return Response({
                'success': False,
                'framework_id': framework.FrameworkId,
                'framework_name': framework.FrameworkName,
                'summary': {
                    'new_controls': 0,
                    'modified_controls': 0,
                    'deprecated_controls': 0,
                    'sub_policies_affected': 0,
                    'total_amendments': 0,
                    'latest_amendment_date': None,
                    'latest_amendment_name': None
                },
                'message': 'No amendments found for this framework.'
            }, status=status.HTTP_200_OK)
        
        latest_amendment = amendments[-1]
        ai_analysis = latest_amendment.get('ai_analysis', {})
        
        # Count statistics
        modified_controls = ai_analysis.get('modified_controls', [])
        new_additions = ai_analysis.get('new_additions', [])
        
        # Count by change type
        modified_count = sum(1 for c in modified_controls if c.get('change_type') in ['modified', 'enhanced'])
        new_count = len(new_additions)
        deprecated_count = sum(1 for c in modified_controls if c.get('change_type') == 'deprecated')
        
        # Count sub-policies affected
        sub_policies_count = sum(
            len(c.get('sub_policies', [])) 
            for c in modified_controls
        )
        
        return Response({
            'success': True,
            'framework_id': framework.FrameworkId,
            'framework_name': framework.FrameworkName,
            'summary': {
                'new_controls': new_count,
                'modified_controls': modified_count,
                'deprecated_controls': deprecated_count,
                'sub_policies_affected': sub_policies_count,
                'total_amendments': len(amendments),
                'latest_amendment_date': latest_amendment.get('uploaded_date'),
                'latest_amendment_name': latest_amendment.get('amendment_name')
            }
        }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching comparison summary for framework {framework_id}: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def find_control_matches(request, framework_id):
    """
    Find best matching origin items for a target control
    
    POST body:
    {
        "control": {
            "control_id": "...",
            "control_name": "...",
            "change_description": "..."
        },
        "use_ai": true/false,  # Optional, default false
        "top_n": 5  # Optional, default 5
    }
    """
    try:
        logger.info("find_control_matches called")
        logger.info("Request user: %s", getattr(request.user, "UserName", None))
        logger.info("Request data: %s", request.data)

        # Get request data
        control = request.data.get('control')
        use_ai = request.data.get('use_ai', False)
        top_n = request.data.get('top_n', 5)
        
        if not control:
            return Response({
                'success': False,
                'error': 'Control data is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get origin data
        framework = Framework.objects.get(FrameworkId=framework_id)
        
        # Get all policies for this framework
        policies = Policy.objects.filter(FrameworkId=framework_id).values(
            'PolicyId',
            'PolicyName',
            'PolicyDescription',
            'Identifier',
            'Status',
            'CurrentVersion'
        )
        
        policies_data = []
        db_compliances = []
        for policy in policies:
            # Get subpolicies for each policy
            subpolicies = SubPolicy.objects.filter(PolicyId=policy['PolicyId']).values(
                'SubPolicyId',
                'SubPolicyName',
                'Description',
                'Identifier',
                'Status'
            )
            
            subpolicies_data = []
            for subpolicy in subpolicies:
                # Get compliances for each subpolicy
                compliances = Compliance.objects.filter(SubPolicy=subpolicy['SubPolicyId']).values(
                    'ComplianceId',
                    'ComplianceTitle',
                    'ComplianceItemDescription',
                    'ComplianceType',
                    'Status'
                )
                
                subpolicies_data.append({
                    **subpolicy,
                    'compliances': list(compliances)
                })
            
            policies_data.append({
                **policy,
                'subpolicies': subpolicies_data
            })
        
        origin_data = {
            'framework': {
                'FrameworkId': framework.FrameworkId,
                'FrameworkName': framework.FrameworkName
            },
            'policies': policies_data
        }
        
        # Get similarity matcher
        matcher = get_similarity_matcher()
        
        # Find matches
        matches = matcher.find_best_matches(
            control,
            origin_data,
            top_n=top_n,
            use_ai=use_ai
        )
        
        return Response({
            'success': True,
            'control': control,
            'matches': matches,
            'total_matches': len(matches),
            'use_ai': use_ai
        }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error finding control matches for framework {framework_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def batch_match_controls(request, framework_id):
    """
    Match multiple controls at once
    
    POST body:
    {
        "controls": [...],  # Array of controls
        "use_ai": true/false  # Optional, default false
    }
    """
    try:
        # Get request data
        controls = request.data.get('controls', [])
        use_ai = request.data.get('use_ai', False)
        
        if not controls:
            return Response({
                'success': False,
                'error': 'Controls array is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get origin data
        framework = Framework.objects.get(FrameworkId=framework_id)
        
        # Get all policies for this framework
        policies = Policy.objects.filter(FrameworkId=framework_id).values(
            'PolicyId',
            'PolicyName',
            'PolicyDescription',
            'Identifier',
            'Status',
            'CurrentVersion'
        )
        
        policies_data = []
        db_compliances = []
        for policy in policies:
            # Get subpolicies for each policy
            subpolicies = SubPolicy.objects.filter(PolicyId=policy['PolicyId']).values(
                'SubPolicyId',
                'SubPolicyName',
                'Description',
                'Identifier',
                'Status'
            )
            
            subpolicies_data = []
            for subpolicy in subpolicies:
                # Get compliances for each subpolicy
                compliances = Compliance.objects.filter(SubPolicy=subpolicy['SubPolicyId']).values(
                    'ComplianceId',
                    'ComplianceTitle',
                    'ComplianceItemDescription',
                    'ComplianceType',
                    'Status'
                )
                
                subpolicies_data.append({
                    **subpolicy,
                    'compliances': list(compliances)
                })
            
            policies_data.append({
                **policy,
                'subpolicies': subpolicies_data
            })
        
        origin_data = {
            'framework': {
                'FrameworkId': framework.FrameworkId,
                'FrameworkName': framework.FrameworkName
            },
            'policies': policies_data
        }
        
        # Get similarity matcher
        matcher = get_similarity_matcher()
        
        # Batch match controls
        results = matcher.batch_match_controls(controls, origin_data, use_ai=use_ai)
        
        return Response({
            'success': True,
            'total_controls': len(controls),
            'matches': results,
            'use_ai': use_ai
        }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error batch matching controls for framework {framework_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_migration_overview(request, framework_id):
    """
    Get migration overview for a framework
    Returns high-level statistics and recent activity
    """
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        amendments = framework.Amendment if framework.Amendment else []
        
        if not amendments:
            return Response({
                'success': False,
                'error': 'No amendments found for this framework'
            }, status=status.HTTP_404_NOT_FOUND)
        
        latest_amendment = amendments[-1]
        ai_analysis = latest_amendment.get('ai_analysis', {})
        
        # Count statistics
        modified_controls = ai_analysis.get('modified_controls', [])
        new_additions = ai_analysis.get('new_additions', [])
        
        # Count by change type
        new_count = len(new_additions)
        modified_count = sum(1 for c in modified_controls if c.get('change_type') in ['modified', 'enhanced'])
        removed_count = sum(1 for c in modified_controls if c.get('change_type') == 'deprecated')
        
        # Calculate progress (this is a simple calculation, can be made more sophisticated)
        total_changes = new_count + modified_count + removed_count
        # Assume if we have processed the latest amendment, we're 80% complete (example)
        progress_percentage = 80 if total_changes > 0 else 0
        
        # Get migration status based on framework status
        migration_status = "IN PROGRESS"
        if framework.Status == "Approved":
            migration_status = "COMPLETED"
        elif framework.Status == "Draft":
            migration_status = "NOT STARTED"
        
        # Generate recent activities from modified controls (latest 5)
        recent_activities = []
        activity_count = 0
        for control in modified_controls[:5]:
            activity_count += 1
            activity = {
                'id': activity_count,
                'action': f"{control.get('control_id', 'N/A')} {control.get('control_name', 'Control')} - {control.get('change_type', 'modified').title()}",
                'status': 'completed' if control.get('change_type') == 'deprecated' else 'info',
                'time': 'Recently updated',
                'control_id': control.get('control_id'),
                'change_type': control.get('change_type')
            }
            recent_activities.append(activity)
        
        return Response({
            'success': True,
            'framework': {
                'id': framework.FrameworkId,
                'name': framework.FrameworkName,
                'version': framework.CurrentVersion,
                'status': framework.Status
            },
            'migration_status': migration_status,
            'progress_percentage': progress_percentage,
            'statistics': {
                'new_controls': new_count,
                'modified_controls': modified_count,
                'removed_controls': removed_count,
                'total_changes': total_changes
            },
            'recent_activities': recent_activities,
            'latest_amendment': {
                'name': latest_amendment.get('amendment_name'),
                'date': latest_amendment.get('uploaded_date'),
                's3_url': latest_amendment.get('s3_url')
            }
        }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching migration overview for framework {framework_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def match_amendments_compliances(request, framework_id):
    """
    Match all compliances from amendments against database compliances
    Uses AI for better matching accuracy
    
    POST body:
    {
        "use_ai": true/false,  # Optional, default true
        "threshold": 0.3  # Optional, minimum similarity score (0.0-1.0)
    }
    """
    try:
        logger.info("match_amendments_compliances called for framework_id: %s", framework_id)
        
        # Get request parameters
        use_ai = request.data.get('use_ai', True)
        threshold = request.data.get('threshold', 0.3)
        print(f"[ComplianceMatch] API invoked | framework_id={framework_id} | use_ai={use_ai} | threshold={threshold}")
        
        # Get framework
        framework = Framework.objects.get(FrameworkId=framework_id)
        amendments = framework.Amendment if framework.Amendment else []
        
        if not amendments:
            return Response({
                'success': False,
                'error': 'No amendments found for this framework'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get latest amendment
        latest_amendment = amendments[-1]
        ai_analysis = latest_amendment.get('ai_analysis', {})
        
        # Prepare amendments data
        amendments_data = {
            'modified_controls': ai_analysis.get('modified_controls', []),
            'new_additions': ai_analysis.get('new_additions', []),
            'framework_references': ai_analysis.get('framework_references', [])
        }
        
        # Get origin data (all compliances from database)
        policies = Policy.objects.filter(FrameworkId=framework_id).values(
            'PolicyId',
            'PolicyName',
            'PolicyDescription',
            'Identifier',
            'Status',
            'CurrentVersion'
        )
        
        policies_data = []
        db_compliances = []
        for policy in policies:
            # Get subpolicies for each policy
            subpolicies = SubPolicy.objects.filter(PolicyId=policy['PolicyId']).values(
                'SubPolicyId',
                'SubPolicyName',
                'Description',
                'Identifier',
                'Status'
            )
            
            subpolicies_data = []
            for subpolicy in subpolicies:
                # Get compliances for each subpolicy
                compliances = Compliance.objects.filter(SubPolicy=subpolicy['SubPolicyId']).values(
                    'ComplianceId',
                    'ComplianceTitle',
                    'ComplianceItemDescription',
                    'ComplianceType',
                    'Status',
                    'Criticality',
                    'MaturityLevel',
                    'ManualAutomatic',
                    'MandatoryOptional'
                )
                compliance_list = list(compliances)
                
                subpolicies_data.append({
                    **subpolicy,
                    'compliances': compliance_list
                })

                for comp in compliance_list:
                    db_compliances.append({
                        'compliance_id': comp.get('ComplianceId'),
                        'title': comp.get('ComplianceTitle') or '',
                        'description': comp.get('ComplianceItemDescription') or '',
                        'type': comp.get('ComplianceType'),
                        'criticality': comp.get('Criticality'),
                        'mandatory': (comp.get('MandatoryOptional') or '').lower() == 'mandatory',
                        'policy_name': policy.get('PolicyName'),
                        'policy_identifier': policy.get('Identifier'),
                        'subpolicy_name': subpolicy.get('SubPolicyName'),
                        'subpolicy_identifier': subpolicy.get('Identifier')
                    })
            
            policies_data.append({
                **policy,
                'subpolicies': subpolicies_data
            })
        
        origin_data = {
            'framework': {
                'FrameworkId': framework.FrameworkId,
                'FrameworkName': framework.FrameworkName
            },
            'policies': policies_data
        }
        
        structured_compliances = _extract_compliances_from_sections(latest_amendment.get('sections', []))
        use_structured_fallback = (
            not amendments_data['modified_controls']
            and not amendments_data['new_additions']
            and structured_compliances
        )

        if use_structured_fallback:
            logger.info("⚙️ Using structured amendment compliances for AI-based matching (fallback mode)")
            print(f"[ComplianceMatch] Falling back to structured sections with AI matching. Targets={len(structured_compliances)}")
            if not db_compliances:
                return Response({
                    'success': False,
                    'error': 'No compliances found in database for this framework'
                }, status=status.HTTP_400_BAD_REQUEST)

            results = _match_compliances_with_ai(
                structured_compliances,
                db_compliances,
                framework.FrameworkName,
                use_ai=use_ai,
                threshold=threshold
            )
        else:
            # Get similarity matcher
            matcher = get_similarity_matcher()
            
            # Match compliances using change-management AI matcher
            results = matcher.match_all_amendments_compliances(
                amendments_data,
                origin_data,
                use_ai=use_ai,
                threshold=threshold
            )
        print(
            "[ComplianceMatch] Completed | total_amendment="
            f"{results['total_target']} | matched={results['matched_count']} | unmatched={results['unmatched_count']}"
        )
        
        return Response({
            'success': True,
            'framework_id': framework.FrameworkId,
            'framework_name': framework.FrameworkName,
            'amendment_id': latest_amendment.get('amendment_id'),
            'amendment_name': latest_amendment.get('amendment_name'),
            'use_ai': use_ai,
            'threshold': threshold,
            'results': results,
            'summary': {
                'total_target_compliances': results['total_target'],
                'total_origin_compliances': results['total_origin'],
                'matched_count': results['matched_count'],
                'unmatched_count': results['unmatched_count'],
                'match_percentage': (results['matched_count'] / results['total_target'] * 100) if results['total_target'] > 0 else 0
            }
        }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error matching compliances for framework {framework_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_migration_gap_analysis(request, framework_id):
    """
    Get gap analysis data for migration
    Returns detailed breakdown of changes needed
    """
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        amendments = framework.Amendment if framework.Amendment else []
        
        if not amendments:
            return Response({
                'success': False,
                'error': 'No amendments found for this framework'
            }, status=status.HTTP_404_NOT_FOUND)
        
        latest_amendment = amendments[-1]
        ai_analysis = latest_amendment.get('ai_analysis', {})
        
        # Get modified controls and new additions
        modified_controls = ai_analysis.get('modified_controls', [])
        new_additions = ai_analysis.get('new_additions', [])
        
        # Format gap items
        gap_items = []
        for control in modified_controls:
            gap_item = {
                'control_id': control.get('control_id'),
                'control_name': control.get('control_name'),
                'change_type': control.get('change_type'),
                'change_description': control.get('change_description'),
                'enhancements': control.get('enhancements', []),
                'related_controls': control.get('related_controls', []),
                'sub_policies': control.get('sub_policies', []),
                'priority': _determine_priority(control.get('change_type')),
                'action_required': _get_action_required(control.get('change_type')),
                'status': 'pending'
            }
            gap_items.append(gap_item)
        
        # Add new additions as gap items
        for addition in new_additions:
            gap_item = {
                'control_id': addition.get('control_id'),
                'control_name': addition.get('control_name'),
                'change_type': 'new',
                'change_description': addition.get('purpose', ''),
                'scope': addition.get('scope'),
                'purpose': addition.get('purpose'),
                'requirements': addition.get('requirements', []),
                'priority': 'High',
                'action_required': 'Implement new control',
                'status': 'new'
            }
            gap_items.append(gap_item)
        
        return Response({
            'success': True,
            'framework': {
                'id': framework.FrameworkId,
                'name': framework.FrameworkName,
                'version': framework.CurrentVersion
            },
            'amendment': {
                'name': latest_amendment.get('amendment_name'),
                'date': latest_amendment.get('uploaded_date')
            },
            'gap_items': gap_items,
            'total_gaps': len(gap_items),
            'summary': {
                'high_priority': sum(1 for item in gap_items if item['priority'] == 'High'),
                'medium_priority': sum(1 for item in gap_items if item['priority'] == 'Medium'),
                'low_priority': sum(1 for item in gap_items if item['priority'] == 'Low'),
                'new_controls': sum(1 for item in gap_items if item['change_type'] == 'new'),
                'modified_controls': sum(1 for item in gap_items if item['change_type'] in ['modified', 'enhanced']),
                'deprecated_controls': sum(1 for item in gap_items if item['change_type'] == 'deprecated')
            }
        }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching gap analysis for framework {framework_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _determine_priority(change_type):
    """Helper function to determine priority based on change type"""
    priority_map = {
        'new': 'High',
        'modified': 'High',
        'enhanced': 'Medium',
        'deprecated': 'Low',
        'unchanged': 'Low'
    }
    return priority_map.get(change_type, 'Medium')


def _get_action_required(change_type):
    """Helper function to get action required based on change type"""
    action_map = {
        'new': 'Implement new control and procedures',
        'modified': 'Review and update existing control',
        'enhanced': 'Enhance existing control implementation',
        'deprecated': 'Plan phaseout and update documentation',
        'unchanged': 'No action required'
    }
    return action_map.get(change_type, 'Review changes')


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def start_amendment_analysis(request, framework_id):
    """
    Manually trigger amendment processing after user has reviewed the document.
    This is called when user clicks "Start Analysis" button.
    NOW SAVES TO DATABASE: Amendment, latestAmmendmentDate, latestComparisionCheckDate
    """
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        
        # Find the most recent PDF in change_management folder
        change_management_dir = os.path.join(settings.MEDIA_ROOT, 'change_management')
        
        if not os.path.exists(change_management_dir):
            return Response({
                'success': False,
                'error': 'No downloaded documents found. Please check for updates first.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Find the most recent PDF file
        pdf_files = []
        for filename in os.listdir(change_management_dir):
            if filename.lower().endswith('.pdf'):
                file_path = os.path.join(change_management_dir, filename)
                if os.path.isfile(file_path):
                    pdf_files.append((file_path, os.path.getmtime(file_path)))
        
        if not pdf_files:
            return Response({
                'success': False,
                'error': 'No PDF document found. Please check for updates and download a document first.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get the most recent PDF
        pdf_files.sort(key=lambda x: x[1], reverse=True)
        document_path = pdf_files[0][0]
        document_name = os.path.basename(document_path)
        
        logger.info(f"Starting manual amendment analysis for framework {framework_id}")
        logger.info(f"Processing document: {document_name}")
        
        # Try to load metadata from JSON file if it exists
        metadata_file = os.path.join(os.path.dirname(document_path), f"{os.path.splitext(document_name)[0]}_metadata.json")
        s3_url = None
        s3_key = None
        s3_stored_name = None
        amendment_date_str = datetime.now().strftime("%Y-%m-%d")
        document_url = None
        
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                s3_url = metadata.get('s3_url')
                s3_key = metadata.get('s3_key')
                s3_stored_name = metadata.get('s3_stored_name')
                amendment_date_str = metadata.get('amendment_date', amendment_date_str)
                document_url = metadata.get('document_url')
                logger.info(f"Loaded metadata from: {metadata_file}")
            except Exception as e:
                logger.warning(f"Could not load metadata file: {str(e)}")
        
        # Get amendment date from request (override metadata if provided)
        amendment_date_str = request.data.get('amendment_date', amendment_date_str)
        
        # Process the amendment
        from .amendment_processor import process_downloaded_amendment
        
        output_dir = change_management_dir
        
        processing_result = process_downloaded_amendment(
            pdf_path=document_path,
            framework_name=framework.FrameworkName,
            framework_id=framework_id,
            amendment_date=amendment_date_str,
            output_dir=output_dir
        )
        
        if processing_result.get('success'):
            # NOW save to database: Amendment, latestAmmendmentDate, latestComparisionCheckDate
            amendment_data = processing_result.get('data', {})
            
            # Parse amendment date
            try:
                latest_date = datetime.strptime(amendment_date_str, "%Y-%m-%d").date()
            except ValueError:
                latest_date = datetime.now().date()
            
            # Get relative path
            relative_path = os.path.relpath(document_path, settings.MEDIA_ROOT)
            
            # Create amendment entry with processed data (S3 info from metadata file)
            new_amendment = {
                'amendment_id': 1,
                'amendment_name': f"{framework.FrameworkName} Amendment - {amendment_date_str}",
                'amendment_date': amendment_date_str,
                'document_path': document_path,
                'document_relative_path': relative_path,
                'document_name': document_name,
                'document_url': document_url,
                's3_url': s3_url,  # From metadata file
                's3_key': s3_key,  # From metadata file
                's3_stored_name': s3_stored_name,  # From metadata file
                'downloaded_date': datetime.now().isoformat(),
                'processed': True,
                'processed_date': datetime.now().isoformat(),
                'extraction_summary': amendment_data.get('extraction_summary', {}),
                'sections': amendment_data.get('sections', []),
                'framework_info': amendment_data.get('amendment_metadata', {}).get('framework_info', {}),
                'ai_analysis': amendment_data.get('ai_analysis', {})
            }
            
            # NOW update Framework table with Amendment and dates
            framework.Amendment = [new_amendment]
            framework.latestAmmendmentDate = latest_date
            framework.latestComparisionCheckDate = timezone.now().date()
            framework.save(update_fields=['Amendment', 'latestAmmendmentDate', 'latestComparisionCheckDate'])
            
            logger.info(f"Successfully processed and saved amendment to database for framework {framework_id}")
            
            return Response({
                'success': True,
                'message': f'Amendment processed and saved successfully. Extracted {amendment_data.get("extraction_summary", {}).get("total_policies", 0)} policies and {amendment_data.get("extraction_summary", {}).get("total_compliance_records", 0)} compliance records.',
                'result': {
                    'total_policies': amendment_data.get('extraction_summary', {}).get('total_policies', 0),
                    'total_subpolicies': amendment_data.get('extraction_summary', {}).get('total_subpolicies', 0),
                    'total_compliance_records': amendment_data.get('extraction_summary', {}).get('total_compliance_records', 0),
                    'output_file': processing_result.get('output_file')
                }
            }, status=status.HTTP_200_OK)
        else:
            logger.error(f"Amendment processing failed for framework {framework_id}: {processing_result.get('error')}")
            return Response({
                'success': False,
                'error': f"Processing failed: {processing_result.get('error', 'Unknown error')}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error starting amendment analysis: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_amendment_document_info(request, framework_id):
    """
    Get information about the downloaded amendment document.
    Returns document name, path, and processing status.
    PRIORITIZES latest downloaded file from change_management folder over database.
    """
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        document_info = None
        document_path = None
        s3_url = None
        
        # PRIORITY 1: Check change_management folder for latest downloaded files FIRST
        # This ensures we always show the most recently downloaded document
        change_management_dir = os.path.join(settings.MEDIA_ROOT, 'change_management')
        
        if os.path.exists(change_management_dir):
            # Find the most recent PDF file
            pdf_files = []
            for filename in os.listdir(change_management_dir):
                if filename.lower().endswith('.pdf'):
                    file_path = os.path.join(change_management_dir, filename)
                    if os.path.isfile(file_path):
                        pdf_files.append((file_path, os.path.getmtime(file_path)))
            
            if pdf_files:
                # Get the most recent PDF (sorted by modification time, newest first)
                pdf_files.sort(key=lambda x: x[1], reverse=True)
                document_path = pdf_files[0][0]
                document_name = os.path.basename(document_path)
                
                # Try to load metadata from JSON file if it exists
                # First, try exact match: {pdf_filename}_metadata.json
                metadata_file = os.path.join(os.path.dirname(document_path), f"{os.path.splitext(document_name)[0]}_metadata.json")
                if not os.path.exists(metadata_file):
                    # Fallback: search for any JSON files that might be metadata
                    pdf_base = os.path.splitext(document_name)[0]
                    for filename in os.listdir(change_management_dir):
                        if filename.lower().endswith('.json') and pdf_base in filename:
                            metadata_file = os.path.join(change_management_dir, filename)
                            logger.info(f"Found alternative metadata file: {metadata_file}")
                            break
                
                if os.path.exists(metadata_file):
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            document_info = json.load(f)
                        logger.info(f"Loaded latest document metadata from: {metadata_file}")
                    except Exception as e:
                        logger.warning(f"Could not load metadata file: {str(e)}")
                        document_info = None
                
                # If no metadata file, create basic document info
                if not document_info:
                    relative_path = os.path.relpath(document_path, settings.MEDIA_ROOT)
                    document_info = {
                        'document_name': document_name,
                        'document_path': document_path,
                        'document_relative_path': relative_path,
                        'downloaded_date': datetime.fromtimestamp(pdf_files[0][1]).isoformat(),
                        'processed': False,
                        's3_url': None
                    }
        
        # PRIORITY 2: Fall back to database (Amendment field) only if no file in change_management folder
        if not document_info:
            amendments = framework.Amendment if framework.Amendment else []
            
            if amendments:
                latest_amendment = amendments[-1]
                document_path = latest_amendment.get('document_path')
                s3_url = latest_amendment.get('s3_url')
                
                # Check if document exists
                has_document = (
                    (document_path and os.path.exists(document_path) and document_path.lower().endswith('.pdf')) or
                    (s3_url is not None)
                )
                
                if has_document:
                    document_info = latest_amendment
                    logger.info(f"Using document from database (Amendment field): {document_path or s3_url}")
        
        # If we have document info, return it
        if document_info:
            # Determine document URL
            # PRIORITY: Always use S3 URL if available (works in all environments)
            if isinstance(document_info, dict) and document_info.get('s3_url'):
                document_url = document_info['s3_url']
                document_source = 's3'
            elif document_path and os.path.exists(document_path):
                # Fallback to local path (works in DEBUG mode or if web server serves /media/)
                # Use os.path.normpath and str() to ensure cross-platform compatibility
                try:
                    relative_path = document_info.get('document_relative_path')
                    if not relative_path:
                        # Convert Path objects to strings for os.path.relpath
                        media_root_str = str(settings.MEDIA_ROOT)
                        document_path_str = str(document_path)
                        relative_path = os.path.relpath(document_path_str, media_root_str)
                    # Normalize path separators for URLs (always use forward slashes)
                    relative_path = relative_path.replace('\\', '/')
                    # Ensure no leading slash in relative_path (MEDIA_URL already has one)
                    relative_path = relative_path.lstrip('/')
                    document_url = f"{settings.MEDIA_URL.rstrip('/')}/{relative_path}"
                    document_source = 'local'
                except Exception as e:
                    logger.warning(f"Error constructing local document URL: {str(e)}")
                    document_url = None
                    document_source = 'unknown'
            else:
                document_url = None
                document_source = 'unknown'
            
            return Response({
                'success': True,
                'has_document': True,
                'framework_id': framework_id,
                'framework_name': framework.FrameworkName,
                'document': {
                    'name': document_info.get('document_name', os.path.basename(document_path) if document_path else 'Unknown'),
                    'path': document_path,
                    'relative_path': document_info.get('document_relative_path'),
                    'url': document_url,  # S3 URL if available, otherwise local URL
                    'source': document_source,  # 's3' or 'local'
                    's3_url': document_info.get('s3_url'),
                    's3_key': document_info.get('s3_key'),
                    'amendment_date': document_info.get('amendment_date'),
                    'downloaded_date': document_info.get('downloaded_date'),
                    'processed': document_info.get('processed', False),
                    'processed_date': document_info.get('processed_date'),
                    'extraction_summary': document_info.get('extraction_summary', {})
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': True,
                'has_document': False,
                'framework_id': framework_id,
                'framework_name': framework.FrameworkName,
                'message': 'No document found. Please check for updates first.'
            }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting document info: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



