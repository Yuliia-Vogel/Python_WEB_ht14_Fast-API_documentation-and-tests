from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date, datetime


class ContactBase(BaseModel): # визначає поля класу Contacts
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    birthday: date
    additional_info: Optional[str] = None


class ContactResponse(ContactBase): # модель відповіді при поверненні даних Contacts клієнту
    id: int
    created_at: datetime
    owner_id: int

    class Config:
        from_attributes = True # цей атрибут використовується для увімкнення режиму ORM для цієї моделі


class ContactUpdate(ContactBase): # для оновлення контакту.
    first_name: Optional[str] # всі поля optional - щоб можна було оновити вибіркові поля
    last_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    birthday: Optional[date]
    additional_info: Optional[str]
    
    class Config:
        from_attributes = True



class UserModel(BaseModel): # для створення юзера
    username: str = Field(min_length=5, max_length=16)
    email: EmailStr
    password: str = Field(min_length=6, max_length=10)


class UserDb(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    avatar: str

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    user: UserDb
    detail: str = "User successfully created"


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr