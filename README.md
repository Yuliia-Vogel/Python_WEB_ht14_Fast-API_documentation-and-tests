# Python_WEB_ht13_REST_API
REST API для зберігання та управління контактами. API повинен бути побудований з використанням інфраструктури FastAPI та використовувати SQLAlchemy для управління базою даних.
Додана авторизація та підтвердження електронної пошти.


1. venv
2. pip install poetry
3. poetry install --no-root 
__
Postgres is used as database, Redis is used for current user cahing. Therefore 2 docker containers should be created.
__
4. Open Docker desktop and CMD. 
__________________________________________________________________
((

4. 1.  Create docker-container for Postgres DB. 
Command in CMD: 
docker pull postgres
docker run --name hw13_base -p 5433:5432 -e POSTGRES_PASSWORD=qwerty123 -e POSTGRES_DB=hw13_base -d postgres
--> command:
docker ps
--> answer:
CONTAINER ID   IMAGE      COMMAND                  CREATED          STATUS          PORTS                    NAMES
f636dccd9d8e   postgres   "docker-entrypoint.s…"   19 seconds ago   Up 18 seconds   0.0.0.0:5433->5432/tcp   hw13_base
4. 2. Create docker-container for Redis.
Command in CMD:
docker pull redis
docker run --name redis-cache -d -p 6379:6379 redis

4. 3. Check in Docker desktop if containers hw13_base and redis-cache are working.
))
---------------------------------------------------------------------------------------------------------
5. Instead of creating 2 docker-containers for Redis and Postgres, use Docker Compose tool - command in terminal:
docker compose up
Wait till multicontainer Docker Compose app is created.
6. Afted Postgres base creation and models.py is ready, perform migration of data to Postgres:
alembic revision --autogenerate -m 'Init'
alembic upgrade head
7. Create file .env in root folder (please see .env.example file)
8. Run the uvicorn server:  uvicorn main:app --reload
9. Готово, можна користуватися - зберігати контакти, переглядати їх, редагувати, видаляти, а також перевіряти, чи є дні народження в найближчі 7 днів.

WARNING!
While performing login, please use your email as a username.

WARNING!
After registration, you should go to your email box and verify your email box for the service before logging in.

Щоб запустити тестування - команда в терміналі з кореневої папки:
python -m unittest tests/repository/test_unit_repository_contacts.py



________________________________
ПРИ РОЗРОБЦІ:
5. 1. alembic init migrations
5. 2. Оскільки ми хочемо використовувати автогенерацію SQL скриптів у міграціях alembic, нам необхідно повідомити про це оточення alembic у файлі env.py, який розташований у папці migrations. Відкриємо його і насамперед імпортуємо нашу декларативну базу Base з файлу models.py та рядок підключення SQLALCHEMY_DATABASE_URL до нашої бази даних.

from src.database.models import Base
from src.database.db import SQLALCHEMY_DATABASE_URL

Далі нам необхідно знайти наступний рядок нижче в коді файлу env.py:

target_metadata = None

і замість None, вказати наші метадані:

target_metadata = Base.metadata

Тут виконаємо заміну рядка підключення до бази даних на актуальну:

config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)
5. 3. Створюємо міграцію наступною консольною командою в корені проекту.

alembic revision --autogenerate -m 'Init'
5. 4. Якщо файл з міграцією успішно створився в папці migrations/versions, то застосуємо створену міграцію:

alembic upgrade head

6. Run the uvicorn server:  uvicorn main:app --reload

7. Готово, можна користуватися - зберігати контакти, переглядати їх, редагувати, видаляти, а також перевіряти, чи є дні народження в найближчі 7 днів.




Винести дані про пошту для розслки в файл .env

ВИПРАВИТИ: при спробі користувачем зберегти контакт з мейлом, і цей мейл уже збережений іншим користувачем -
випадає помилка. Потрібно зробити так, щоб ця перевірка на унікальність мейлів відбувалася на рівні одного користувача, а не по всій таблиця збережених контактів.

Ми реалізували скидання пароля користувача для застосунку Django. Для застосунку FastAPI логіка поведінки 
буде точно така сама, як і для застосунку Django. За необхідності ми можемо самостійно реалізувати 
верифікацію email користувача в застосунку REST API. Пропонуємо вам виконати це самостійно.