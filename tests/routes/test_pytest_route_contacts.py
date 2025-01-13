from unittest.mock import MagicMock
import pytest
from src.database.models import User
from src.services.auth import auth_service


@pytest.fixture()
def token(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    client.post("/api/auth/signup", json=user)
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')},
    )
    data = response.json()
    return data["access_token"]


def test_create_contact(client, token):
    new_contact = {
        "first_name": "Test_Name",
        "last_name": "Last_Name",
        "email": "test.contact@example.com",
        "phone": "+1234567890",
        "birthday": "1990-01-01",
        "additional_info": "123 Test Street, Test City",
    }

    response = client.post(
        "/api/contacts",
        json=new_contact,
        headers={"Authorization": f"Bearer {token}"},
        params={"args": "value", "kwargs": "value"}
    )

    # Перевіряємо статус відповіді
    assert response.status_code == 201, response.text

    # Перевіряємо дані у відповіді
    data = response.json()
    assert "id" in data
    assert data["first_name"] == new_contact["first_name"]
    assert data["last_name"] == new_contact["last_name"]
    assert data["email"] == new_contact["email"]
    assert data["phone"] == new_contact["phone"]
    assert data["birthday"] == new_contact["birthday"]
    assert data["additional_info"] == new_contact["additional_info"]
    assert "created_at" in data
    assert "owner_id" in data
