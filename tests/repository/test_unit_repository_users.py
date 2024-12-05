import datetime
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.orm import Session

from src.database.models import User
from src.schemas import UserModel, UserDb, UserResponse
from src.repository.users import (
    get_user_by_email,
    create_user,
    update_token,
    confirmed_email,
    update_avatar
    )


class TestUsers(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)


    async def test_get_user_by_email_found(self):
        #   тестові дані:
        users = [
            User(id=1, email="test_1@example.com"),
            User(id=2, email="test_2@example.com"),
            User(id=3, email="test_3@example.com")
        ]

        # Налаштовуємо мок: filter().first() має повернути користувача з email="test_2@example.com"
        def filter_side_effect(*args, **kwargs):
            # Емуляція фільтрації за email
            email_filter = kwargs.get("email", None)
            for user in users:
                if user.email == email_filter:
                    return user
            return None

         # Симулюємо поведінку filter().first()
        self.session.query().filter().first.side_effect = lambda: next(
            (user for user in users if user.email == "test_2@example.com"), None
        )

        # Викликаємо функцію
        result = await get_user_by_email(email="test_2@example.com", db=self.session)

        # Перевіряємо, що знайдено саме потрібного користувача
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 2)
        self.assertEqual(result.email, "test_2@example.com")


    async def test_get_user_by_email_not_found(self):
        #    тестові дані:
        users = [
            User(id=1, email="test_1@example.com"),
            User(id=2, email="test_2@example.com"),
            User(id=3, email="test_3@example.com")
        ]

        # Налаштовуємо мок: filter().first() має повернути користувача з певним email
        def filter_side_effect(*args, **kwargs):
            # Емуляція фільтрації за email
            email_filter = kwargs.get("email", None)
            for user in users:
                if user.email == email_filter:
                    return user
            return None

        # мейл, який ми шукаємо (немає в списку):
        expected_email = "test_4@example.com"

        # Налаштовуємо поведінку filter().first() для симуляції пошуку
        self.session.query().filter().first.side_effect = lambda: next(
            (user for user in users if user.email == expected_email), None
            )

        # Викликаємо функцію
        result = await get_user_by_email(email=expected_email, db=self.session)

        # Перевіряємо, що результат - None, - користувача з зазначеним мейлом не знайдено
        self.assertIsNone(result)


    async def test_get_user_by_email_empty_database(self):
        # Налаштовуємо мок: filter().first() повертає None, оскільки база порожня
        self.session.query().filter().first.return_value = None

        # Email, який ми шукаємо
        email_to_find = "test@example.com"

        # Викликаємо функцію для пошуку користувача
        result = await get_user_by_email(email=email_to_find, db=self.session)

        # Перевіряємо, що результат — None (користувача не знайдено)
        self.assertIsNone(result)


    @patch("src.repository.users.Gravatar")
    async def test_create_user_with_avatar(self, mock_gravatar):
        body = UserModel(
                         id=1,
                         username="AnnaAl", 
                         email="test@mail.com", 
                         password="annaa_pass"
                        )
        
        # Мок Gravatar
        mock_gravatar_instance = mock_gravatar.return_value
        mock_gravatar_instance.get_image.return_value = "http://gravatar.com/avatar/mockavatar"

        # Моковий об'єкт new_user:
        new_user = User(
            id=None, # спочатку None
            username=body.username,
            email=body.email,
            password=body.password,
            avatar=None, # спочатку None
            created_at=None, # спочатку None
        )
        # Налаштування мок-об'єкта:
        self.session.add.return_value = None # імітація додавання даних в базу даних, return_value = None - щоб нічого зайвого не робилося 
        self.session.commit.return_value = None # імітація коміту в базу даних
        
        avatar_url = "http://gravatar.com/avatar/mockavatar"

        # Симулюємо поведінку db.refresh(new_user)
        def mock_refresh(user):
            user.id = 1  # Призначаємо моковий ID
            user.created_at = datetime.datetime.now()  # Призначаємо моковий час створення
            user.avatar = avatar_url  # Призначаємо моковий аватар

        self.session.refresh.side_effect = mock_refresh # моковий "рефреш": додає user_id i created_at до нашого тествого юзера
        
        # Виклик функції
        result = await create_user(body=body, db=self.session)

        # Оновлюємо new_user після рефрешу
        mock_refresh(new_user)

        # Перевірка результату
        self.assertEqual(result.id, 1)
        self.assertEqual(result.username, new_user.username)
        self.assertEqual(result.email, new_user.email)
        self.assertEqual(result.password, new_user.password)
        self.assertIsNotNone(result.created_at)
        self.assertEqual(result.created_at, new_user.created_at)
        self.assertEqual(result.avatar, avatar_url)


    @patch("src.repository.users.Gravatar")
    async def test_create_user_no_avatar(self, mock_gravatar):
        body = UserModel(
                         id=1,
                         username="AnnaAl", 
                         email="test@mail.com", 
                         password="annaa_pass"
                        )
        
        # Мок Gravatar
        mock_gravatar_instance = mock_gravatar.return_value
        mock_gravatar_instance.get_image.side_effect = Exception("Gravatar service error")

        # Моковий об'єкт new_user:
        new_user = User(
            id=None, # спочатку None
            username=body.username,
            email=body.email,
            password=body.password,
            avatar=None, # спочатку None
            created_at=None, # спочатку None
        )
        # Налаштування мок-об'єкта:
        self.session.add.return_value = None # імітація додавання даних в базу даних, return_value = None - щоб нічого зайвого не робилося 
        self.session.commit.return_value = None # імітація коміту в базу даних

        # Симулюємо поведінку db.refresh(new_user)
        def mock_refresh(user):
            user.id = 1  # Призначаємо моковий ID
            user.created_at = datetime.datetime.now()  # Призначаємо моковий час створення
            user.avatar = None  # Через помилку аватар залишається None

        self.session.refresh.side_effect = mock_refresh # моковий "рефреш": додає user_id i created_at до нашого тествого юзера
        
        # Виклик функції
        result = await create_user(body=body, db=self.session)

        # Оновлюємо new_user після рефрешу
        mock_refresh(new_user)

        # Перевірка результату
        self.assertEqual(result.id, 1)
        self.assertEqual(result.username, new_user.username)
        self.assertEqual(result.email, new_user.email)
        self.assertEqual(result.password, new_user.password)
        self.assertIsNotNone(result.created_at)
        self.assertEqual(result.created_at, new_user.created_at)
        self.assertIsNone(result.avatar)  # Перевіряємо, що аватар залишився None

    async def test_update_token(self):
        # створюю тествого юзера:
        user = User(id=5, username="Anna_An", email="anna_an@gmail.com", refresh_token=None)

        # new token:
        new_token = "the_new_refresh_token"

        # викликаю функцію:
        result = await update_token(user=user, token=new_token, db=self.session)

        # Перевірка, чи оновлено токен
        self.assertEqual(user.refresh_token, new_token)

        # Перевірка, чи викликано commit
        self.session.commit.assert_called_once()


    async def test_update_token_if_token_is_none(self):
        user = User(id=5, username="Anna_An", email="anna_an@gmail.com", refresh_token="refresh_token_exists")
        new_token=None
        result = await update_token(user=user, token=new_token, db=self.session)
        # Перевіряємо, що refresh_token змінено на None
        self.assertIsNone(user.refresh_token)
        # Перевіряємо, що commit викликано
        self.session.commit.assert_called_once()


    async def test_update_token_calls_commit(self):
        user = User(id=5, username="Anna_An", email="anna_an@gmail.com", refresh_token=None)
        new_token="refresh_token"
        result = await update_token(user=user, token=new_token, db=self.session)
        # Перевіряємо, що refresh_token оновлено
        self.assertEqual(user.refresh_token, new_token)
        # Перевіряємо, що commit викликано
        self.session.commit.assert_called_once()


    @patch("src.repository.users.get_user_by_email", new_callable=AsyncMock) 
    async def test_confirmed_email(self, mock_get_user_by_email): # В unittest, коли використовується @patch, параметри для мока додаються перед аргументами self
        email = "test@email.net"
        # тестовий юзер:
        user = User(id=1, email=email, confirmed=False)
        mock_get_user_by_email.return_value = user  # Емуляція повернення користувача
        # Виклик функції
        await confirmed_email(email=email, db=self.session)

        # Перевірка, що get_user_by_email викликано із правильними параметрами
        mock_get_user_by_email.assert_called_once_with(email, self.session)

        # Перевіряємо, що статус user.confirmed оновлено до True:
        self.assertTrue(user.confirmed)
        # Перевіряємо, що commit викликано
        self.session.commit.assert_called_once()

    @patch("src.repository.users.get_user_by_email")
    async def test_update_avatar(self, mock_get_user_by_email):
        email = "test@email.com"
        new_avatar_url = "http://new.avatar.url"
        
        # тестовий юзер:
        user = User(id=1, email=email, avatar="http://old.avatar.url")
        
        # Мокаємо get_user_by_email, щоб він повертав тестового юзера:
        mock_get_user_by_email.return_value = user
        
        # Виклик функції для оновлення аватарки:
        result = await update_avatar(email=email, url=new_avatar_url, db=self.session)

        # Перевірка, чи функція get_user_by_email викликається з правильними параметрами
        mock_get_user_by_email.assert_called_once_with(email, self.session)
        
        # Перевірка, чи аватарка оновилась:
        self.assertEqual(result.avatar, new_avatar_url)

        # Перевірка, чи був викликаний commit 
        self.session.commit.assert_called_once()


    