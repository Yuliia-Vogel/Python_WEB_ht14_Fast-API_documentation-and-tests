from libgravatar import Gravatar
from sqlalchemy.orm import Session

from src.database.models import User
from src.schemas import UserModel
 

async def get_user_by_email(email: str, db: Session) -> User | None:
    """
    Retrieves a single user with the specified email.

    :param email: The email of the user to retrieve.
    :type email: str
    :param db: The database session.
    :type db: Session
    :return: The user with the specified email, or None if no such user exists.
    :rtype: User | None
    """
    return db.query(User).filter(User.email == email).first()


async def create_user(body: UserModel, db: Session) -> User:
    """
    Creates a new user.

    :param body: The data for the user to create.
    :type body: UserModel
    :param db: The database session.
    :type db: Session
    :return: The newly created user.
    :rtype: User
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(e)
    new_user = User(**body.dict(), avatar=avatar)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: Session) -> None:
    """
    Updates the refresh token of the specified user in the current session.

    :param user: The user whose refresh token will be updated.
    :type user: User
    :param token: The new refresh token for the user. Can be None to clear the token.
    :type token: str | None
    :param db: The database session.
    :type db: Session
    :return: None
    """
    user.refresh_token = token
    db.commit()


async def confirmed_email(email: str, db: Session) -> None:
    """
    Marks the user's email as confirmed.

    :param email: The email of the user to confirm.
    :type email: str
    :param db: The database session.
    :type db: Session
    :raises ValueError: If no user is found with the specified email.
    :return: None
    """
    user = await get_user_by_email(email, db)
    if not user: # added raise error during docstring adding
        raise ValueError(f"User with email {email} does not exist.")
    user.confirmed = True
    db.commit()


async def update_avatar(email: str, url: str, db: Session) -> User:
    """
    Updates the avatar URL for the specified user.

    :param email: The email of the user whose avatar will be updated.
    :type email: str
    :param url: The URL of the new avatar image.
    :type url: str
    :param db: The database session.
    :type db: Session
    :raises ValueError: If no user is found with the specified email.
    :return: The user whose avatar was updated.
    :rtype: User
    """
    user = await get_user_by_email(email, db)
    if not user: # added raise error during docstring adding
        raise ValueError(f"User with email {email} does not exist.")
    user.avatar = url
    db.commit()
    return user