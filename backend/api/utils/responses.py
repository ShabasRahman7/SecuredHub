from rest_framework.response import Response
from rest_framework import status

def success_response(message, data=None, status_code=status.HTTP_200_OK):
    # creating a standardized success response.
    response_data = {
        "success": True,
        "message": message
    }
    
    if data is not None:
        response_data["data"] = data
    
    return Response(response_data, status=status_code)

def error_response(message, details=None, status_code=status.HTTP_400_BAD_REQUEST):
    # creating a standardized error response.
    response_data = {
        "success": False,
        "error": {
            "message": message
        }
    }
    
    if details is not None:
        response_data["error"]["details"] = details
    
    return Response(response_data, status=status_code)
