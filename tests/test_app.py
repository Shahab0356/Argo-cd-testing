import pytest
from app.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    """Test that the home page loads successfully"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'EKS Demo Application' in response.data

def test_health_endpoint(client):
    """Test the health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'timestamp' in data
    assert 'version' in data

def test_api_info_endpoint(client):
    """Test the API info endpoint"""
    response = client.get('/api/info')
    assert response.status_code == 200
    data = response.get_json()
    assert data['application'] == 'EKS Demo App'
    assert data['technology'] == 'Python Flask'
    assert 'timestamp' in data

def test_404_error(client):
    """Test that non-existent routes return 404"""
    response = client.get('/nonexistent')
    assert response.status_code == 404
