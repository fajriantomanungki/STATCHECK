def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login_and_read_profile(client):
    login = client.post("/api/v1/auth/login", json={"nik": "admin", "password": "Admin123!"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    profile = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.json()["nik"] == "admin"


def test_rejects_invalid_password(client):
    response = client.post("/api/v1/auth/login", json={"nik": "admin", "password": "password-salah"})
    assert response.status_code == 401


def test_profile_requires_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401
