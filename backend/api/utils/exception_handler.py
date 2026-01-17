from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    
    if response is not None:
        custom_response_data = {
            'success': False,
            'error': {
                'message': str(exc),
                'details': response.data if isinstance(response.data, dict) else {'detail': response.data}
            }
        }
        response.data = custom_response_data
    else:
        try:
            import traceback
            traceback.print_exc()
        except Exception:
            pass
        response = Response(
            {
                'success': False,
                'error': {
                    'message': 'An unexpected error occurred.',
                    'details': 'Internal server error'
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return response
