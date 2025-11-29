from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
import logging

logger = logging.getLogger('api')


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint to verify API is running and database is accessible.
    """
    response_data = {
        'success': True,
        'status': 'ok',
        'message': 'API is running',
        'database': 'disconnected'
    }
    
    # Check database connection
    try:
        connection.ensure_connection()
        response_data['database'] = 'connected'
        logger.info("Health check passed")
        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as e:
        response_data['success'] = False
        response_data['status'] = 'degraded'
        response_data['message'] = 'API is running but database is unavailable'
        response_data['error'] = str(e)
        logger.error(f"Health check failed: {e}")
        return Response(response_data, status=status.HTTP_503_SERVICE_UNAVAILABLE)
