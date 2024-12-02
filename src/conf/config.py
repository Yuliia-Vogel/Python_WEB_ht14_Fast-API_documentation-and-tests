from pydantic import EmailStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    sqlalchemy_database_url: str
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_port: int
    secret_key: str
    algorithm: str
    mail_username: str
    mail_password: str
    mail_from: EmailStr
    mail_from_name: str
    mail_port: int
    mail_server: str
    redis: str
    redis_host: str = 'localhost'
    redis_port: int = 6379
    cloudinary_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings() # створили об"єкт класу Settings, з якого будемо вставляти дані по проекту