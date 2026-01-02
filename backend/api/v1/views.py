from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import connection

class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        response_data = {
            'success': True,
            'status': 'ok',
            'message': 'API is running',
            'database': 'disconnected'
        }
        
        try:
            connection.ensure_connection()
            response_data['database'] = 'connected'
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            response_data['success'] = False
            response_data['status'] = 'degraded'
            response_data['message'] = 'API is running but database is unavailable'
            response_data['error'] = str(e)
            return Response(response_data, status=status.HTTP_503_SERVICE_UNAVAILABLE)

health_check = HealthCheckView.as_view()
