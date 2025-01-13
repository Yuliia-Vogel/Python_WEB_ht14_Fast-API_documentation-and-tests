import pytest
import fakeredis # без цього в мене ну ніяк не мокався Редіс

from unittest.mock import MagicMock, patch

from src.database.models import User
# from src.services.auth import auth_service


@pytest.fixture
def mock_redis():
    # Створюємо мок Redis
    fake_redis = fakeredis.FakeStrictRedis()
    with patch("src.services.auth.redis.StrictRedis", return_value=fake_redis):
        yield fake_redis


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


# @patch("src.services.auth.auth_service.r", new_callable=fakeredis.FakeStrictRedis)
# def test_create_contact(mock_redis, client, token):
#      # Тепер r.get() у auth_service використовує моканий Redis
#     mock_redis.set("user:test.contact@example.com", "mocked_value")

#     new_contact = {
#         "first_name": "Test_Name",
#         "last_name": "Last_Name",
#         "email": "test.contact@example.com",
#         "phone": "+1234567890",
#         "birthday": "1990-01-01",
#         "additional_info": "123 Test Street, Test City",
#     }

#     response = client.post(
#         "/api/contacts",
#         json=new_contact,
#         headers={"Authorization": f"Bearer {token}"},
#         params={"args": "value", "kwargs": "value"}
#     )

#     # Перевіряємо статус відповіді
#     assert response.status_code == 201, response.text
    
#     # Перевіряємо дані у відповіді
#     data = response.json()
#     assert "id" in data
#     assert data["first_name"] == new_contact["first_name"]
#     assert data["last_name"] == new_contact["last_name"]
#     assert data["email"] == new_contact["email"]
#     assert data["phone"] == new_contact["phone"]
#     assert data["birthday"] == new_contact["birthday"]
#     assert data["additional_info"] == new_contact["additional_info"]
#     assert "created_at" in data
#     assert "owner_id" in data


# # Оскільки в роуті contacts функцію "src.repository.contacts.read_contact" імпортовано як "repository_contacts",
# # то в мене тепер при тестуванні виникла проблема, що мок адекватно не передається в роут замість функції
# # з репозиторію contacts.read_contact, а якщо назвати мок точно як в роуті - то пайтон не може знайти такий шлях
# # "src.repository.repository_contacts.read_contact". Вирішенням стало досягти мокування ДО початку всього даного 
# # тесту - з допомогою додатикового патчу patch("src.repository.contacts.read_contact"):
# @patch("src.repository.contacts.read_contact")
# @patch("src.services.auth.auth_service.r", new_callable=fakeredis.FakeStrictRedis)
# def test_read_contact(mock_redis, mock_read_contact, client, token):
#     # Налаштовуємо мок Redis
#     mock_redis.set("user:test.contact@example.com", "mocked_value")

#     # ID контакту, який ми хочемо отримати
#     contact_id = 1

#     # Моканий контакт, який мав би повернути репозиторій
#     mocked_contact = {
#         "id": contact_id,
#         "first_name": "Test",
#         "last_name": "User",
#         "email": "test.user@example.com",
#         "phone": "+1234567890",
#         "birthday": "1990-01-01",
#         "additional_info": "Some additional info",
#         "created_at": "2025-01-01",
#         "owner_id": 1
#     }

#     # Мокаємо репозиторій для повернення контакту
#     mock_read_contact.return_value = mocked_contact

#     # Виконуємо запит до роута
#     response = client.get(
#         f"/api/contacts/{contact_id}",
#         headers={"Authorization": f"Bearer {token}"}
#     )
    
#     # Перевіряємо статус відповіді
#     assert response.status_code == 200, response.text
#     # Перевіряємо дані у відповіді
#     data = response.json()
#     assert data["id"] == mocked_contact["id"]
#     assert data["first_name"] == mocked_contact["first_name"]
#     assert data["last_name"] == mocked_contact["last_name"]
#     assert data["email"] == mocked_contact["email"]
#     assert data["phone"] == mocked_contact["phone"]
#     assert data["birthday"] == mocked_contact["birthday"]
#     assert data["additional_info"] == mocked_contact["additional_info"]
#     assert "created_at" in data
#     assert "owner_id" in data


# @patch("src.repository.contacts.read_contact")
# @patch("src.services.auth.auth_service.r", new_callable=fakeredis.FakeStrictRedis)
# def test_get_contact_not_found(mock_redis, mock_read_contact, client, token):
#     # Налаштовуємо мок Redis
#     mock_redis.set("user:test.contact@example.com", "mocked_value")

#     # ID неіснуючого контакту
#     contact_id = 2

#     # Мокаємо репозиторій для повернення None
#     mock_read_contact.return_value = None

#     # Виконуємо запит до роута
#     response = client.get(
#         f"/api/contacts/{contact_id}",
#         headers={"Authorization": f"Bearer {token}"}
#     )
    
#     # Перевіряємо статус відповіді
#     assert response.status_code == 404, response.text
    
#     # Перевіряємо дані у відповіді
#     data = response.json()
#     assert data["detail"] == f"Contact {contact_id} not found"


# @patch("src.repository.contacts.get_contacts")
# @patch("src.services.auth.auth_service.r", new_callable=fakeredis.FakeStrictRedis)
# def test_get_contacts(mock_redis, mock_get_contacts, client, token):
#     # Налаштовуємо мок Redis
#     mock_redis.set("user:test.contact@example.com", "mocked_value")
    
#     # Мокані контакти, які відповідатимуть моделі ContactResponse
#     contact_1 = {
#         "id": 1,
#         "first_name": "Name1",
#         "last_name": "Last1",
#         "email": "last_name_1@gmail.com",
#         "phone": "+1234567890",
#         "birthday": "1999-01-01",
#         "additional_info": "Test address 1, Test City1",
#         "created_at": "2025-01-01T00:00:00",
#         "owner_id": 1
#     }
#     contact_2 = {
#         "id": 2,
#         "first_name": "Name2",
#         "last_name": "Last2",
#         "email": "last_name_2@mail.com",
#         "phone": "+2345678901",
#         "birthday": "1921-01-01",
#         "additional_info": "Test address 2, Test City2",
#         "created_at": "2025-01-02T00:00:00",
#         "owner_id": 1
#     }

#     mocked_list_of_contacts = [contact_1, contact_2]

#     # Мокаємо репозиторій для повернення контакту
#     mock_get_contacts.return_value = mocked_list_of_contacts

#     response = client.get(
#             "/api/contacts",
#             headers={"Authorization": f"Bearer {token}"},
#             params={"args": "value", "kwargs": "value"}
#         )
#     assert response.status_code == 200, response.text
#     data = response.json()
#     assert isinstance(data, list)
#     assert data[0]["id"] == contact_1["id"]
#     assert data[0]["first_name"] == contact_1["first_name"]
#     assert data[0]["last_name"] == contact_1["last_name"]
#     assert data[0]["email"] == contact_1["email"]
#     assert data[0]["phone"] == contact_1["phone"]
#     assert data[0]["birthday"] == contact_1["birthday"]
#     assert data[0]["additional_info"] == contact_1["additional_info"]
#     assert data[0]["created_at"] == contact_1["created_at"]
#     assert data[0]["owner_id"] == contact_1["owner_id"]

#     assert data[1]["id"] == contact_2["id"]
#     assert data[1]["first_name"] == contact_2["first_name"]
#     assert data[1]["last_name"] == contact_2["last_name"]
#     assert data[1]["email"] == contact_2["email"]
#     assert data[1]["phone"] == contact_2["phone"]
#     assert data[1]["birthday"] == contact_2["birthday"]
#     assert data[1]["additional_info"] == contact_2["additional_info"]
#     assert data[1]["created_at"] == contact_2["created_at"]
#     assert data[1]["owner_id"] == contact_2["owner_id"]


@patch("src.repository.contacts.get_upcoming_birthdays")
@patch("src.services.auth.auth_service.r", new_callable=fakeredis.FakeStrictRedis)
def test_get_upcoming_birthdays(mock_redis, mock_get_upcoming_birthdays, client, token):
    # Налаштовуємо мок Redis
    mock_redis.set("user:test.contact@example.com", "mocked_value")
    
    # контакт, що відповідатиме моделі ContactResponse
    contact_bd = {
        "id": 1,
        "first_name": "NameBD",
        "last_name": "LastBD",
        "email": "last_name_BD@gmail.com",
        "phone": "+1234567890",
        "birthday": "1999-11-11",
        "additional_info": "Test address BD, Test City",
        "created_at": "2020-01-01T00:00:00",
        "owner_id": 1
    }
    # модель відповіді List[ContactResponse]
    mocked_list = [contact_bd]

    # Мокаємо репозиторій для повернення контакту
    mock_get_upcoming_birthdays.return_value = mocked_list
    
    response = client.get(
            "/api/contacts/birthdays",
            headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["id"] == contact_bd["id"]
    assert data[0]["first_name"] == contact_bd["first_name"]
    assert data[0]["last_name"] == contact_bd["last_name"]
    assert data[0]["email"] == contact_bd["email"]
    assert data[0]["phone"] == contact_bd["phone"]
    assert data[0]["birthday"] == contact_bd["birthday"]
    assert data[0]["additional_info"] == contact_bd["additional_info"]
    assert data[0]["created_at"] == contact_bd["created_at"]
    assert data[0]["owner_id"] == contact_bd["owner_id"]

