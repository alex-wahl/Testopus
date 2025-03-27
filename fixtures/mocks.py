import json
from unittest.mock import patch
import pytest

class ResponseMock:
    """Mock HTTP responses for API calls"""
    
    @staticmethod
    def json_response(status_code=200, data=None):
        """Create a mock response with JSON data"""
        mock_response = type('MockResponse', (), {})()
        mock_response.status_code = status_code
        mock_response.json = lambda: data or {}
        mock_response.text = json.dumps(data or {})
        return mock_response


@pytest.fixture
def api_mock():
    """Fixture that mocks API responses"""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post, \
         patch('requests.put') as mock_put, \
         patch('requests.delete') as mock_delete:
        
        # Set default return values
        mock_get.return_value = ResponseMock.json_response()
        mock_post.return_value = ResponseMock.json_response()
        mock_put.return_value = ResponseMock.json_response()
        mock_delete.return_value = ResponseMock.json_response()
        
        # Create a helper object to simplify configuration
        mock_api = type('MockAPI', (), {})()
        mock_api.get = mock_get
        mock_api.post = mock_post
        mock_api.put = mock_put
        mock_api.delete = mock_delete
        
        # Helper to set quick responses
        def set_json_response(method, url, data, status_code=200):
            method_map = {
                'get': mock_get,
                'post': mock_post,
                'put': mock_put,
                'delete': mock_delete
            }
            mock_method = method_map.get(method.lower())
            if mock_method:
                mock_method.return_value = ResponseMock.json_response(
                    status_code=status_code, data=data
                )
        
        mock_api.set_json_response = set_json_response

        yield mock_api
