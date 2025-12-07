from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import connection
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from ...rbac.permissions import RiskViewPermission

@api_view(['GET'])
@permission_classes([RiskViewPermission])  # RBAC: Require RiskViewPermission for viewing risk versions
def get_all_versions(request, risk_id):
    """
    Get all versions for a specific risk ID
    Returns list of versions with their data for comparison
    """
    print(f"\n=== GET ALL VERSIONS CALLED ===")
    print(f"Risk ID: {risk_id}")
    print(f"Risk ID type: {type(risk_id)}")
    
    try:
        with connection.cursor() as cursor:
            # First, let's check if there's any data in the table at all
            cursor.execute("SELECT COUNT(*) FROM grc.risk_approval")
            total_count = cursor.fetchone()[0]
            print(f"Total records in risk_approval table: {total_count}")
            
            # Check if there are any records for this specific risk ID
            cursor.execute("SELECT COUNT(*) FROM grc.risk_approval WHERE RiskInstanceId = %s", [risk_id])
            risk_count = cursor.fetchone()[0]
            print(f"Records for RiskInstanceId {risk_id}: {risk_count}")
            
            # Let's also see what RiskInstanceIds exist in the table
            cursor.execute("SELECT DISTINCT RiskInstanceId FROM grc.risk_approval LIMIT 10")
            existing_ids = cursor.fetchall()
            print(f"Existing RiskInstanceIds (first 10): {[row[0] for row in existing_ids]}")
            
            cursor.execute("""
                SELECT RiskInstanceId, version, ExtractedInfo, UserId, ApproverId, 
                       Date, ApprovedRejected
                FROM grc.risk_approval 
                WHERE RiskInstanceId = %s
                ORDER BY version
            """, [risk_id])
            
            rows = cursor.fetchall()
            print(f"Found {len(rows)} versions in database for risk {risk_id}")
            
            versions = []
            version_names = []  # New list to store just the version names
            
            for i, row in enumerate(rows):
                print(f"\n--- Processing Version {i+1} ---")
                print(f"RiskInstanceId: {row[0]}")
                print(f"Version: {row[1]}")
                print(f"UserId: {row[3]}")
                print(f"ApproverId: {row[4]}")
                print(f"Date: {row[5]}")
                print(f"ApprovedRejected: {row[6]}")
                print(f"ExtractedInfo length: {len(row[2]) if row[2] else 0} characters")
                
                # Add version name to the list
                if row[1]:  # Make sure version is not None
                    version_names.append(row[1])
                
                version_data = {
                    'RiskInstanceId': row[0],
                    'version': row[1],
                    'ExtractedInfo': row[2],
                    'UserId': row[3],
                    'ApproverId': row[4],
                    'Date': row[5],
                    'ApprovedRejected': row[6],
                    'formatted_date': row[5].strftime('%Y-%m-%d %H:%M:%S') if row[5] else None
                }
                
                # Parse ExtractedInfo if it's a JSON string
                if version_data['ExtractedInfo']:
                    try:
                        extracted_data = json.loads(version_data['ExtractedInfo'])
                        version_data['mitigations'] = extracted_data.get('mitigations', {})
                        version_data['risk_form_details'] = extracted_data.get('risk_form_details', {})
                        
                        print(f"Mitigations found: {list(version_data['mitigations'].keys()) if version_data['mitigations'] else 'None'}")
                        print(f"Risk form details keys: {list(version_data['risk_form_details'].keys()) if version_data['risk_form_details'] else 'None'}")
                        
                        # Print detailed mitigation data
                        if version_data['mitigations']:
                            for mit_id, mit_data in version_data['mitigations'].items():
                                print(f"  Mitigation {mit_id}:")
                                print(f"    Description: {mit_data.get('description', 'N/A')[:100]}...")
                                print(f"    Status: {mit_data.get('status', 'N/A')}")
                                print(f"    Approved: {mit_data.get('approved', 'N/A')}")
                                print(f"    Comments: {mit_data.get('comments', 'N/A')[:50]}...")
                        
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        version_data['mitigations'] = {}
                        version_data['risk_form_details'] = {}
                else:
                    print("No ExtractedInfo data")
                    version_data['mitigations'] = {}
                    version_data['risk_form_details'] = {}
                
                versions.append(version_data)
            
            print(f"\n=== RETURNING {len(versions)} VERSIONS ===")
            print(f"Version names: {version_names}")
            return Response({
                'success': True,
                'versions': versions,
                'version_names': version_names,  # Add the list of version names
                'total_versions': len(versions),
                'debug_info': {
                    'total_records_in_table': total_count,
                    'records_for_risk_id': risk_count,
                    'existing_risk_ids': [row[0] for row in existing_ids]
                }
            })
    except Exception as e:
        print(f"ERROR in get_all_versions: {e}")
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([RiskViewPermission])  # RBAC: Require RiskViewPermission for viewing specific risk version
def get_previous_version(request, risk_id, version):
    """
    Get detailed information for a specific version
    """
    print(f"\n=== GET PREVIOUS VERSION CALLED ===")
    print(f"Risk ID: {risk_id}")
    print(f"Requested Version: {version}")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT RiskInstanceId, version, ExtractedInfo, UserId, ApproverId
                FROM grc.risk_approval 
                WHERE RiskInstanceId = %s AND version = %s
            """, [risk_id, version])
            
            row = cursor.fetchone()
            
            if row:
                print(f"Version found in database:")
                print(f"  RiskInstanceId: {row[0]}")
                print(f"  Version: {row[1]}")
                print(f"  UserId: {row[3]}")
                print(f"  ApproverId: {row[4]}")
                print(f"  ExtractedInfo length: {len(row[2]) if row[2] else 0} characters")
                
                version_data = {
                    'RiskInstanceId': row[0],
                    'version': row[1],
                    'ExtractedInfo': row[2],
                    'UserId': row[3],
                    'ApproverId': row[4]
                }
                
                # Parse ExtractedInfo if it's a JSON string
                if version_data['ExtractedInfo']:
                    try:
                        parsed_data = json.loads(version_data['ExtractedInfo'])
                        version_data['ExtractedInfo'] = parsed_data
                        
                        print(f"Parsed ExtractedInfo successfully:")
                        print(f"  Keys: {list(parsed_data.keys()) if isinstance(parsed_data, dict) else 'Not a dict'}")
                        
                        if 'mitigations' in parsed_data:
                            print(f"  Mitigations: {list(parsed_data['mitigations'].keys())}")
                            for mit_id, mit_data in parsed_data['mitigations'].items():
                                print(f"    Mitigation {mit_id}:")
                                print(f"      Description: {mit_data.get('description', 'N/A')[:100]}...")
                                print(f"      Status: {mit_data.get('status', 'N/A')}")
                                print(f"      Approved: {mit_data.get('approved', 'N/A')}")
                                print(f"      User submitted date: {mit_data.get('user_submitted_date', 'N/A')}")
                        
                        if 'risk_form_details' in parsed_data:
                            print(f"  Risk form details: {list(parsed_data['risk_form_details'].keys())}")
                        
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        print(f"Raw ExtractedInfo: {version_data['ExtractedInfo'][:200]}...")
                
                print(f"=== RETURNING VERSION DATA ===")
                return JsonResponse({
                    'success': True,
                    'version_data': version_data
                })
            else:
                print(f"Version {version} NOT FOUND for risk {risk_id}")
                return JsonResponse({
                    'success': False,
                    'message': 'Version not found',
                    'version_data': None
                }, status=404)
                
    except Exception as e:
        print(f"ERROR in get_previous_version: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e),
            'version_data': None
        }, status=500)

@api_view(['GET'])
@permission_classes([RiskViewPermission])  # RBAC: Require RiskViewPermission for comparing risk versions
def get_version_comparison(request, risk_id, version1, version2):
    """
    Compare two specific versions of a risk
    Returns detailed comparison data
    """
    print(f"\n=== GET VERSION COMPARISON CALLED ===")
    print(f"Risk ID: {risk_id}")
    print(f"Version 1: {version1}")
    print(f"Version 2: {version2}")
    
    try:
        with connection.cursor() as cursor:
            # Get both versions
            cursor.execute("""
                SELECT RiskInstanceId, version, ExtractedInfo, UserId, ApproverId
                FROM grc.risk_approval 
                WHERE RiskInstanceId = %s AND version IN (%s, %s)
                ORDER BY version ASC
            """, [risk_id, version1, version2])
            
            rows = cursor.fetchall()
            print(f"Found {len(rows)} versions for comparison")
            
            versions = []
            
            for i, row in enumerate(rows):
                print(f"\n--- Comparison Version {i+1} ---")
                print(f"Version: {row[1]}")
                
                version_data = {
                    'RiskInstanceId': row[0],
                    'version': row[1],
                    'ExtractedInfo': row[2],
                    'UserId': row[3],
                    'ApproverId': row[4]
                }
                
                # Parse ExtractedInfo
                if version_data['ExtractedInfo']:
                    try:
                        extracted_data = json.loads(version_data['ExtractedInfo'])
                        version_data['mitigations'] = extracted_data.get('mitigations', {})
                        version_data['risk_form_details'] = extracted_data.get('risk_form_details', {})
                        
                        print(f"  Mitigations: {list(version_data['mitigations'].keys())}")
                        print(f"  Form details: {list(version_data['risk_form_details'].keys())}")
                        
                    except json.JSONDecodeError as e:
                        print(f"  JSON decode error: {e}")
                        version_data['mitigations'] = {}
                        version_data['risk_form_details'] = {}
                else:
                    print("  No ExtractedInfo data")
                    version_data['mitigations'] = {}
                    version_data['risk_form_details'] = {}
                
                versions.append(version_data)
        
        # Ensure we have exactly 2 versions
        if len(versions) != 2:
            print(f"ERROR: Expected 2 versions, found {len(versions)}")
            return JsonResponse({
                'success': False,
                'error': f'Expected 2 versions, found {len(versions)}',
                'comparison': None
            }, status=400)
        
        print(f"=== RETURNING COMPARISON DATA ===")
        return JsonResponse({
            'success': True,
            'comparison': {
                'version1': versions[0],
                'version2': versions[1],
                'risk_id': risk_id
            }
        })
        
    except Exception as e:
        print(f"ERROR in get_version_comparison: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e),
            'comparison': None
        }, status=500)
