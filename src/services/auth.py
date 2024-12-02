import pickle
from typing import Optional

import redis
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.repository import users as repository_users

from src.conf.config import settings


class Auth:
    """
    Auth class handles authentication, token creation, and user validation.

    This class provides methods for password hashing, generating access/refresh tokens,
    decoding tokens, and verifying user identity through email confirmation.
    """
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.secret_key
    ALGORITHM = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
    r = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)

    def verify_password(self, plain_password, hashed_password):
        """
        Verifies if the plain password matches the hashed password.

        :param plain_password: The password provided by the user.
        :type plain_password: str
        :param hashed_password: The stored hashed password.
        :type hashed_password: str
        :return: True if passwords match, False otherwise.
        :rtype: bool
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        Hashes the password using the bcrypt algorithm.

        :param password: The plain password to be hashed.
        :type password: str
        :return: The hashed password.
        :rtype: str
        """
        return self.pwd_context.hash(password)

    # define a function to generate a new access token
    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        Creates an access token for the user.

        :param data: The data to encode in the access token (e.g., user information).
        :type data: dict
        :param expires_delta: The expiration time for the access token in seconds (optional).
        :type expires_delta: Optional[float]
        :return: The encoded access token.
        :rtype: str
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token

    # define a function to generate a new refresh token
    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        Creates a refresh token for the user.

        :param data: The data to encode in the refresh token (e.g., user information).
        :type data: dict
        :param expires_delta: The expiration time for the refresh token in seconds (optional).
                            If not provided, the token will expire in 7 days.
        :type expires_delta: Optional[float]
        :return: The encoded refresh token.
        :rtype: str
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        """
        Decodes the refresh token to get the associated user's email.

        :param refresh_token: The refresh token to decode.
        :type refresh_token: str
        :return: The email of the user if the token is valid.
        :rtype: str
        :raises HTTPException: If the token is invalid or has an invalid scope.
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        """
        Retrieves the current user based on the provided access token.

        This method validates the token, extracts the user's email, and retrieves the user 
        information from Redis or the database. If the user is not found or the token is invalid, 
        an HTTPException is raised.

        :param token: The access token provided by the user.
        :type token: str
        :param db: The database session dependency.
        :type db: Session
        :raises HTTPException: If the token is invalid or the user is not found.
        :return: The user object.
        :rtype: User (or equivalent model object, depending on your implementation).
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode JWT
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception

        user = self.r.get(f"user:{email}")
        if user is None:
            user = await repository_users.get_user_by_email(email, db)
            if user is None:
                raise credentials_exception
            self.r.set(f"user:{email}", pickle.dumps(user))
            self.r.expire(f"user:{email}", 900)
        else:
            user = pickle.loads(user)
        return user
    

    def create_email_token(self, data: dict):
        """
        Creates an email verification token.

        This token is used to verify the user's email address and is valid for 7 days.

        :param data: The data to encode in the token (e.g., user email).
        :type data: dict
        :return: The encoded email token.
        :rtype: str
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token
    

    async def get_email_from_token(self, token: str):
        """
        Decodes an email verification token to retrieve the user's email address.

        :param token: The email verification token to decode.
        :type token: str
        :raises HTTPException: If the token is invalid or cannot be decoded.
        :return: The email address extracted from the token.
        :rtype: str
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                          detail="Invalid token for email verification")

auth_service = Auth()