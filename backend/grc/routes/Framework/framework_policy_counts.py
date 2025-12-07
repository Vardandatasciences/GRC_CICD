from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from ...models import Framework, Policy
from ...rbac.permissions import PolicyViewPermission
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])
def get_framework_policy_counts(request, framework_id):
    """
    Get counts of active and inactive policies for a specific framework
    """
    try:
        # Check if framework exists
        try:
            framework = Framework.objects.get(FrameworkId=framework_id)
        except Framework.DoesNotExist:
            return Response({
                'error': f'Framework with ID {framework_id} does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get policy counts
        active_policies = Policy.objects.filter(
            FrameworkId=framework_id,
            ActiveInactive='Active'
        ).count()
        
        inactive_policies = Policy.objects.filter(
            FrameworkId=framework_id,
            ActiveInactive='Inactive'
        ).count()
        
        return Response({
            'framework_id': framework_id,
            'active_policies': active_policies,
            'inactive_policies': inactive_policies,
            'total_policies': active_policies + inactive_policies
        })
        
    except Exception as e:
        logger.error(f"Error getting policy counts for framework {framework_id}: {str(e)}")
        return Response({
            'error': f'Failed to get policy counts: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 