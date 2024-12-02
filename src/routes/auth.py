from typing import List

from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import UserModel, UserResponse, TokenModel, RequestEmail
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.services.email import send_email

router = APIRouter(prefix='/auth', tags=["auth"])
security = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, 
                 background_tasks: BackgroundTasks, 
                 request: Request, 
                 db: Session = Depends(get_db)):
    """
    Creates a new user for the API.

    :http method: POST
    :path: /signup
    :param body: The data required to create a new user.
    :type body: UserModel
    :param background_tasks: Background tasks to handle post-signup actions (e.g., sending emails).
    :type background_tasks: BackgroundTasks
    :param request: The HTTP request object, used to retrieve the base URL for constructing email links.
    :type request: Request
    :param db: The database session.
    :type db: Session
    :raises HTTPException: If a user with the specified email already exists.
    :return: A response containing the newly created user's details and a confirmation message.
    :rtype: UserResponse
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(send_email, new_user.email, new_user.username, request.base_url)
    return {"user": new_user, "detail": "User successfully created. Check your email for confirmation."}


@router.post("/login", response_model=TokenModel)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authorizes the user and generates access and refresh tokens.

    :http method: POST
    :path: /login
    :param body: Represents a form containing login credentials (`username` and `password`) used for OAuth2 authentication.
    :type body: OAuth2PasswordRequestForm
    :param db: The database session.
    :type db: Session
    :raise HTTPException:
        - If the email is not found in the database.
        - If the email is not confirmed.
        - If the password is incorrect.
    :return: A dictionary containing the access token, refresh token, and token type.
    :rtype: TokenModel
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security), 
                        db: Session = Depends(get_db)):
    """
    Refreshes the authentication tokens for the current user session.

    :http method: GET
    :path: /refresh_token
    :param credentials: The user's authorization credentials containing the refresh token.
    :type credentials: HTTPAuthorizationCredentials
    :param db: The database session.
    :type db: Session
    :raises HTTPException: If the provided refresh token is invalid or does not match the stored token.
    :return: A dictionary containing the access token, refresh token, and token type.
    :rtype: TokenModel
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    Confirms the user's email address using a verification token.

    :http method: GET
    :path: /confirmed_email/{token}
    :param token: The verification token sent to the user's email.
    :type token: str
    :param db: The database session.
    :type db: Session
    :raises HTTPException: If the token is invalid or the user does not exist.
    :return: A dictionary containing a confirmation message.
    :rtype: dict
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: Session = Depends(get_db)):
    """
    Initiates the process of confirming a user's email address by sending a confirmation email.

    If the email is already confirmed, it returns a message indicating that. 
    If the email exists in the database but is not confirmed, a confirmation email is sent.

    :http method: POST
    :path: /request_email
    :param body: The request body containing the user's email to request a confirmation email.
    :type body: RequestEmail
    :param background_tasks: Allows for sending the confirmation email as a background task.
    :type background_tasks: BackgroundTasks
    :param request: The incoming HTTP request used to construct the base URL for the confirmation link.
    :type request: Request
    :param db: The database session.
    :type db: Session
    :raises HTTPException: If no user is found with the specified email.
    :return: A message indicating whether the email is confirmed or a confirmation email has been sent.
    :rtype: dict
    """
    user = await repository_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, request.base_url)
    return {"message": "Check your email for confirmation."}