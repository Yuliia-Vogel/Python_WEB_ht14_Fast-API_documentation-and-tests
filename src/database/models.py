# для створення таблиць у базі даних, тому всі поля мають бути описані саме для ств.таблиці

from sqlalchemy import Column, Integer, String, Date, func, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    birthday = Column(Date)
    additional_info = Column(String, nullable=True)
    created_at = Column('created_at', DateTime, default=func.now())

    owner_id = Column(Integer, ForeignKey('users.id'))  # додавання зовнішнього ключа для зв'язку з User
    owner = relationship("User", back_populates="contacts")  # зв'язок з юзерами

    
class User(Base): # створила для авторизації
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(250), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    created_at = Column('created_at', DateTime, default=func.now())
    avatar = Column(String(225), nullable=True)
    refresh_token = Column(String(225), nullable=True)
    confirmed = Column(Boolean, default=False)

    contacts = relationship("Contact", back_populates="owner")
