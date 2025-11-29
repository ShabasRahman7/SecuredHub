from rest_framework.response import Response
from rest_framework import status


def success_response(message, data=None, status_code=status.HTTP_200_OK):
    """
    Create a standardized success response.
    
    Args:
        message (str): Success message
        data (dict, optional): Response data payload
        status_code (int): HTTP status code (default: 200)
    
    Returns:
        Response: DRF Response object with success format
    
    Example:
        return success_response("User created", {"user_id": 1}, status.HTTP_201_CREATED)
    """
    response_data = {
        "success": True,
        "message": message
    }
    
    if data is not None:
        response_data["data"] = data
    
    return Response(response_data, status=status_code)


def error_response(message, details=None, status_code=status.HTTP_400_BAD_REQUEST):
    """
    Create a standardized error response.
    
    Args:
        message (str): Error message
        details (dict or str, optional): Additional error details
        status_code (int): HTTP status code (default: 400)
    
    Returns:
        Response: DRF Response object with error format
    
    Example:
        return error_response("Validation failed", {"email": "Invalid format"}, status.HTTP_400_BAD_REQUEST)
    """
    response_data = {
        "success": False,
        "error": {
            "message": message
        }
    }
    
    if details is not None:
        response_data["error"]["details"] = details
    
    return Response(response_data, status=status_code)
