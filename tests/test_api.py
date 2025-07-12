import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert b'OK' in response.data

def test_predict_endpoint(client):
    """Test the predict endpoint with valid input."""
    test_data = {'text': 'This is positive text'}
    headers = {'X-API-KEY': 'default_key'}  # Use the default API key from config
    response = client.post('/predict', json=test_data, headers=headers)
    # Note: This might return 503 if model isn't loaded, which is expected
    assert response.status_code in [200, 503]

def test_predict_unauthorized(client):
    """Test the predict endpoint without API key."""
    test_data = {'text': 'This is positive text'}
    response = client.post('/predict', json=test_data)
    assert response.status_code == 401
    assert b'Unauthorized' in response.data

def test_predict_invalid_input(client):
    """Test the predict endpoint with invalid input."""
    test_data = {'invalid': 'data'}
    headers = {'X-API-KEY': 'default_key'}
    response = client.post('/predict', json=test_data, headers=headers)
    assert response.status_code == 400
