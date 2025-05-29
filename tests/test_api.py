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
    response = client.post('/predict', json=test_data)
    assert response.status_code == 200
