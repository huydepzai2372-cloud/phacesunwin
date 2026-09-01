from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_google_login_route_is_available():
    response = client.get('/auth/google/login', follow_redirects=False)
    assert response.status_code in (302, 400)


def test_google_callback_requires_invalid_or_missing_state():
    response = client.get('/auth/google/callback', follow_redirects=False)
    assert response.status_code in (400, 302)
