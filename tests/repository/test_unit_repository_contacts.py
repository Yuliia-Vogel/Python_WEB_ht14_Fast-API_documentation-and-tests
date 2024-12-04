import datetime

import unittest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from src.database.models import Contact, User
from src.schemas import ContactBase, ContactUpdate
from src.repository.contacts import (
    get_contacts,
    read_contact,
    create_contact,
    remove_contact,
    update_contact,
    get_upcoming_birthdays
)


class TestContacts(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=1)

    async def test_get_contacts(self):
        contacts = [Contact(id=1), Contact(id=2), Contact(id=3)] # тестові дані
        self.session.query.return_value.filter.return_value.all.return_value = contacts # Налаштування мок-об'єкта
        # Виклик функції
        result = await get_contacts(db=self.session, user=self.user, first_name=None, last_name=None, email=None)
        # Перевірка результату
        self.assertEqual(result, contacts)

    async def test_read_contact_found(self):
        contact = Contact()
        self.session.query.return_value.filter.return_value.first.return_value = contact
        result = await read_contact(contact_id=1, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_read_contact_not_found(self):
        self.session.query.return_value.filter.return_value.first.return_value = None
        result = await read_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_create_contact(self):
        body = ContactBase(id=1, 
                           first_name="TestName", 
                           last_name="TestLastname", 
                           email="test_test@mail.com", 
                           phone="+370999994545", 
                           birthday="1984-12-12", 
                           additional_info="Test info")
        
        # Моковий об'єкт new_contact
        new_contact = Contact(
            id=None,  # Спочатку ID пустий
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            phone=body.phone,
            birthday=body.birthday,
            additional_info=body.additional_info,
            created_at=None,  # Спочатку пусто
            owner_id=self.user.id
        )
        # Налаштування мок-об'єкта
        self.session.add.return_value = None # імітація додавання даних в базу даних, return_value = None - щоб нічого зайвого не робилося 
        self.session.commit.return_value = None # імітація коміту в базу даних
            
        # Симулюємо поведінку db.refresh(new_contact)
        def mock_refresh(contact):
            contact.id = 1  # Призначаємо моковий ID
            contact.created_at = datetime.datetime.now()  # Призначаємо моковий час створення

        self.session.refresh.side_effect = mock_refresh # моковий "рефреш": додає contact_id i created_at до нашого тествого контакту

        # Виклик функції
        result = await create_contact(body=body, user=self.user, db=self.session)

        # Перевірка результату
        self.assertEqual(result.id, 1)
        self.assertEqual(result.first_name, new_contact.first_name)
        self.assertEqual(result.last_name, new_contact.last_name)
        self.assertEqual(result.email, new_contact.email)
        self.assertEqual(result.phone, new_contact.phone)
        self.assertEqual(result.birthday, new_contact.birthday)
        self.assertEqual(result.additional_info, new_contact.additional_info)
        self.assertIsNotNone(result.created_at)
        self.assertEqual(result.owner_id, new_contact.owner_id)

    async def test_remove_contact_found(self):
        contact = Contact()
        self.session.query.return_value.filter.return_value.first.return_value = contact
        result = await remove_contact(contact_id=1, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_remove_contact_not_found(self):
        self.session.query.return_value.filter.return_value.first.return_value = None
        result = await remove_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_update_contact_found(self):
        # дані для тесту, які ми "вносимо" для зміни ісеуючого контакту
        contact_id = 1
        body = ContactUpdate(
            first_name="UpdatedFirstName",
            last_name="UpdatedLastName",
            email="updated@example.com",
            phone="1234567890",
            birthday="2000-01-01",
            additional_info="Updated info"
        )
        # існуючий контакт
        contact = Contact(
            id=contact_id,
            first_name="OldFirstName",
            last_name="OldLastName",
            email="old@example.com",
            phone="0987654321",
            birthday="1990-01-01",
            additional_info="Old info",
            owner_id=self.user.id
        )
        # Мок даних
        self.session.query.return_value.filter.return_value.first.return_value = contact

        # Виклик функції
        result = await update_contact(contact_id=contact_id, body=body, user=self.user, db=self.session)

        # Перевірки
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.birthday, body.birthday)
        self.assertEqual(result.additional_info, body.additional_info)

        # Перевірка, що commit і refresh були викликані
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(contact)

    async def test_update_contact_not_found(self):
        # Вхідні дані для тесту
        contact_id = 1
        body = ContactUpdate(
            first_name="UpdatedFirstName",
            last_name="UpdatedLastName",
            email="updated@example.com",
            phone="1234567890",
            birthday="2000-01-01",
            additional_info="Updated info"
        )
        # Імітуємо, що контакт не знайдено
        self.session.query().filter().first.return_value = None

        # Виклик функції
        result = await update_contact(contact_id=contact_id, body=body, user=self.user, db=self.session)

        # Перевірка, що результат None
        self.assertIsNone(result)

        # Перевірка, що методи commit і refresh не були викликані
        self.session.commit.assert_not_called()
        self.session.refresh.assert_not_called()

    async def test_get_upcoming_birthdays_found(self):
        # визначаємо сьогоднішню дату і діапазон, в який потрапляють ДН контактів:
        today = datetime.date.today()
        # upcomming = today + datetime.timedelta(days=7)
        
        # створюємо список тестових контактів:
        contacts = [
            Contact(id=1, birthday=today + datetime.timedelta(days=3), owner_id=self.user.id),
            Contact(id=2, birthday=today + datetime.timedelta(days=6), owner_id=self.user.id),
            Contact(id=3, birthday=today - datetime.timedelta(days=1), owner_id=self.user.id),  # День народження минув
            Contact(id=4, birthday=today + datetime.timedelta(days=10), owner_id=self.user.id), # Поза межами 7 днів
        ]

        self.session.query().filter().all.return_value = contacts

        # Виклик функції
        result = await get_upcoming_birthdays(user=self.user, db=self.session)

        # прописуємо, які очікувані результати:
        expected_ids = [1, 2]  # Тільки контакти з ДН у межах 7 днів

        # Перевірка
        self.assertEqual(len(result), len(expected_ids))
        self.assertCountEqual([contact.id for contact in result], expected_ids)


    async def test_get_upcoming_birthdays_not_found(self):
        # визначаємо сьогоднішню дату і діапазон, в який потрапляють ДН контактів:
        today = datetime.date.today()
        
        # Імітуємо список контактів (жоден не має ДН у межах 7 днів)
        contacts = [
            Contact(id=1, birthday=today - datetime.timedelta(days=10), owner_id=self.user.id),  # День народження минув
            Contact(id=2, birthday=today + datetime.timedelta(days=15), owner_id=self.user.id), # Поза межами 7 днів
        ]
        self.session.query().filter().all.return_value = contacts

        # Виклик функції
        result = await get_upcoming_birthdays(user=self.user, db=self.session)

        # Очікуваний результат - пустий список
        self.assertEqual(result, [])




if __name__ == '__main__':
    unittest.main()