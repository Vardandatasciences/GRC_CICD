import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ...models import Users, Department, BusinessUnit, Entity, Location
from ...rbac.utils import RBACUtils

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def get_user_business_info(request, user_id):
    try:
        # Get user's department ID
        user = Users.objects.get(UserId=user_id)
        department_id = user.DepartmentId

        # Get department info with related data using raw SQL for efficient joins
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    d.DepartmentName,
                    d.DepartmentHead,
                    bu.Name as BusinessUnitName,
                    e.EntityName,
                    CONCAT(l.AddressLine, ', ', l.City, ', ', l.State, ', ', l.Country) as Location
                FROM department d
                LEFT JOIN businessunits bu ON d.BusinessUnitId = bu.BusinessUnitId
                LEFT JOIN mainentities e ON d.EntityId = e.Id
                LEFT JOIN locations l ON e.LocationId = l.LocationID
                WHERE d.DepartmentId = %s
            """, [department_id])
            
            columns = [col[0] for col in cursor.description]
            result = dict(zip(columns, cursor.fetchone()))

            # Get department head name
            if result['DepartmentHead']:
                dept_head = Users.objects.filter(UserId=result['DepartmentHead']).first()
                if dept_head:
                    result['DepartmentHead'] = f"{dept_head.FirstName} {dept_head.LastName}"

        return JsonResponse({
            'status': 'success',
            'data': result
        })

    except Users.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'User not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@require_http_methods(["GET"])
def get_user_profile(request, user_id):
    try:
        logger.debug(f"Fetching user profile for user_id: {user_id}")
        user = Users.objects.get(UserId=user_id)
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'firstName': user.FirstName,
                'lastName': user.LastName,
                'email': user.Email,
                'username': user.UserName,
                'isActive': user.IsActive,
                'departmentId': user.DepartmentId
            }
        })

    except Users.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'User not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500) 




@api_view(['GET'])
def get_current_user(request):
    """
    Returns the current logged-in user's details including their role from session
    """
    try:
        # Get user details from session using RBAC utils
        user_id = RBACUtils.get_user_id_from_request(request)
        
        if not user_id:
            return Response(
                {'error': 'User not authenticated or session expired'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get RBAC record which contains role and username
        rbac_record = RBACUtils.get_user_rbac_record(user_id)
        
        if not rbac_record:
            return Response(
                {'error': 'No RBAC record found for user'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user_data = {
            'UserId': user_id,
            'UserName': rbac_record.username,
            'role': rbac_record.role,
            'permissions': RBACUtils.get_user_permissions_summary(user_id)
        }
        
        print("Constructed user_data:", user_data)
        
        return Response(user_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch user details: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )