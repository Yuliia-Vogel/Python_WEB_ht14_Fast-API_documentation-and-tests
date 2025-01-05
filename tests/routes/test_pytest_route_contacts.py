import pytest

from unittest.mock import AsyncMock, MagicMock, patch

from src.database.models import User
from src.services.auth import auth_service
from src.schemas import ContactBase
from src.routes.contacts import RateLimiter
from src.services.auth import Auth

import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
from src.conf.config import settings


print("!-!-!*_*_*_*_*_*_* \n RateLimiter:", dir(RateLimiter))
# зараз тести працюють з використанням редіса, який знаходиться в Докер-композі.
# закоментовані нижче фікстури - це те, що пропонує чат-GPT для того, щоб замокати редіс, але поки нічого не 
# виходить, маю помилку: 
# AttributeError: 'type' object at src.routes.contacts.RateLimiter has no attribute 'r'

# @pytest.fixture
# def mock_redis():
#     mock_r = MagicMock()
#     # Mock Redis methods
#     mock_r.get = MagicMock(return_value=None)
#     mock_r.set = MagicMock()
#     mock_r.expire = MagicMock()
#     return mock_r


# @pytest.fixture
# def mock_auth_service(mock_redis):
#     with patch.object(auth_service, 'r', mock_redis):
#         yield auth_service


# @pytest.fixture(autouse=True)
# def mock_redis_global(monkeypatch, mock_redis):
#     monkeypatch.setattr("src.services.auth.auth_service.r", mock_redis)
#     monkeypatch.setattr("src.routes.contacts.RateLimiter.r", mock_redis)


# @pytest.mark.asyncio
# async def test_get_current_user_with_mocked_redis(mock_auth_service):
#     # Example token and mocked user data
#     token = "example_valid_token"
#     mock_user = {"email": "test@example.com", "id": 1}
#     mock_db = MagicMock()

#     # Mock repository method
#     with patch('src.repository.users.get_user_by_email', AsyncMock(return_value=mock_user)):
#         result = await mock_auth_service.get_current_user(token, db=mock_db)

#     assert result['email'] == "test@example.com"
#     mock_auth_service.r.get.assert_called_once()
#     mock_auth_service.r.set.assert_called_once()
#     mock_auth_service.r.expire.assert_called_once()


# @pytest.fixture(autouse=True)
# def mock_dependencies(monkeypatch, mock_redis):
#     # Мокання Redis
#     monkeypatch.setattr("src.services.auth.auth_service.r", mock_redis)
#     monkeypatch.setattr("src.routes.contacts.RateLimiter.r", mock_redis)

#     # Мокання RateLimiter
#     monkeypatch.setattr("src.routes.contacts.RateLimiter.__call__", MagicMock(return_value=None))


@pytest.fixture(autouse=True) # довелося ще й тут дублювати мокання лімітера...
def mock_rate_limiter(monkeypatch):
    monkeypatch.setattr("src.routes.contacts.RateLimiter.__call__", MagicMock(return_value=None))


@pytest.fixture()
def token_and_user(client, user, session, monkeypatch):
    # Відключаємо автоматичне "від'єднання" після commit
    session.expire_on_commit = False

    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    # Реєстрація нового користувача
    client.post("/api/auth/signup", json=user)

    # Отримання користувача після коміту
    session.commit()
    current_user: User = session.query(User).filter(User.email == user.get("email")).one()
    current_user.confirmed = True
    session.add(current_user)  # Додаємо, щоб зафіксувати зміни
    session.commit()
    
    # Авторизація користувача
    response = client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    data = response.json()
    print(f"\n !--!--!--!--!--!--!--!--!--! \n Current user: {current_user.email}, {current_user} \n")
    print("data['access_token'] from fixture", data["access_token"])
    return data["access_token"], current_user


def test_rate_limiter_mocked(client): # тестовий тест :-)))
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to my Fast API web-application!"}



def test_rate_limiter_mock(): # ще один тестовий тест :-)))
    with patch.object(RateLimiter, "__call__", return_value=None):
        limiter = RateLimiter(times=5, seconds=60)
        assert limiter() is None


def test_create_contact(client, token_and_user):
    token, expected_user = token_and_user
        # Виводимо токен для діагностики
    print("Token in test:", token)

    # Додаємо діагностику перед запитом
    # Мокаємо `get_current_user`, щоб повертати створеного користувача
    with patch("src.services.auth.Auth.get_current_user", return_value=expected_user) as mock_get_user:
        # Перевіряємо, що мок повертає очікуваного користувача
        user = mock_get_user.return_value
        print("Current user in test:", user)
        assert user.email == expected_user.email  # Перевірка, чи це той самий користувач
        assert user.id == expected_user.id

    new_contact = {
        "first_name": "Test_Name",
        "last_name": "Last_Name",
        "email": "test.contact@example.com",
        "phone": "+1234567890",
        "birthday": "1990-01-01",
        "additional_info": "123 Test Street, Test City",
    }

    # Надсилаємо запит на створення контакту
    response = client.post(
        "/api/contacts",
        json=new_contact,
        headers={"Authorization": f"Bearer {token}"},
        params={"args": "value", "kwargs": "value"}
    )

    # Діагностичні принти
    print("Response status code:", response.status_code)
    print("Response JSON:", response.json())
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