import pytest
from app import app
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
def test_hello(client):
    response = client.get('/hello?name=Duoc')
    assert response.status_code == 200
    assert b"Duoc" in response.data
