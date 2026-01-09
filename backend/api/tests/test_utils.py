# unit tests for API utility functions
import pytest
from unittest.mock import Mock
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotFound
from api.utils.exception_handler import custom_exception_handler
from api.utils.responses import success_response, error_response


@pytest.mark.unit
class TestExceptionHandler:
    # testing custom exception handler
    
    def test_handles_drf_validation_error(self):
        # should format DRF ValidationError with custom structure
        exc = ValidationError({'email': ['This field is required.']})
        context = {'view': Mock(), 'request': Mock()}
        
        response = custom_exception_handler(exc, context)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert 'error' in response.data
        assert 'message' in response.data['error']
    
    def test_handles_not_found_error(self):
        # should format NotFound error properly
        exc = NotFound('Object not found')
        context = {'view': Mock(), 'request': Mock()}
        
        response = custom_exception_handler(exc, context)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['success'] is False
        assert 'Object not found' in str(response.data['error']['message'])
    
    def test_handles_unexpected_exception(self):
        # should handle unexpected exceptions with 500 response
        exc = RuntimeError('Unexpected error')
        context = {'view': Mock(), 'request': Mock()}
        
        response = custom_exception_handler(exc, context)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['success'] is False
        assert 'unexpected error' in response.data['error']['message'].lower()


@pytest.mark.unit
class TestResponseUtils:
    # testing standardized response utilities
    
    def test_success_response_with_data(self):
        # should create success response with data
        response = success_response(
            message='User created successfully',
            data={'user_id': 123, 'email': 'test@example.com'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['message'] == 'User created successfully'
        assert response.data['data']['user_id'] == 123
    
    def test_success_response_without_data(self):
        # should create success response without data field
        response = success_response(message='Action completed')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['message'] == 'Action completed'
        assert 'data' not in response.data
    
    def test_success_response_custom_status_code(self):
        # should use custom status code
        response = success_response(
            message='Created',
            data={'id': 1},
            status_code=status.HTTP_201_CREATED
        )
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_error_response_with_details(self):
        # should create error response with details
        response = error_response(
            message='Validation failed',
            details={'email': 'Invalid email format'}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert response.data['error']['message'] == 'Validation failed'
        assert response.data['error']['details']['email'] == 'Invalid email format'
    
    def test_error_response_without_details(self):
        # should create error response without details
        response = error_response(message='Authentication required')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert response.data['error']['message'] == 'Authentication required'
        assert 'details' not in response.data['error']
    
    def test_error_response_custom_status_code(self):
        # should use custom error status code
        response = error_response(
            message='Not found',
            status_code=status.HTTP_404_NOT_FOUND
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
