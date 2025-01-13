from typing import List

from fastapi import APIRouter, HTTPException, Depends, status, Query, Request
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User
from src.schemas import ContactBase, ContactResponse, ContactUpdate
from src.repository import contacts as repository_contacts
from src.services.auth import auth_service


router = APIRouter(prefix='/contacts', tags=["contacts"]) # до цього apі-роутера будемо звертатися далі для створення роутів


@router.get("/birthdays", response_model=list[ContactResponse]) # для пошуку днів народж. у найбл. 7 днів. Цю функцію слід ставити перед ф-цією пошуку контакту за {contact_id}, інакше фаст-апі проводить пошук саме за {contact_id}, а не днем народження
async def get_upcoming_birthdays(db: Session = Depends(get_db), 
                                 current_user: User = Depends(auth_service.get_current_user)):
    """
    Retrieves a list of contacts for the authenticated user whose birthdays fall within the next 7 days.

    :http method: GET
    :path: /birthdays
    :param db: The database session.
    :type db: Session
    :param current_user: The currently authenticated user.
    :type current_user: User
    :raises HTTPException: If no upcoming birthdays are found.
    :return: A list of contacts with upcoming birthdays.
    :rtype: list[ContactResponse]
    """
    bd_contacts = await repository_contacts.get_upcoming_birthdays(current_user, db)
    if not bd_contacts:
        raise HTTPException(status_code=404, detail="No upcoming birthdays")
    return bd_contacts


@router.get("/", response_model=List[ContactResponse], description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def get_contacts(request: Request,
                       skip: int = 0, limit: int = 20, db: Session = Depends(get_db),
                       current_user: User = Depends(auth_service.get_current_user),
                       first_name: str | None = Query(None), 
                       last_name: str | None = Query(None),
                       email: str | None = Query(None)): # Додаємо параметр request для того, щоб уникнути проблем при розпаковці отриманих даних в тестах pytest
    """
    Retrieves a list of contacts for the authenticated user. Supports optional filtering by first name, last name, or email.

    :http method: GET
    :path: /
    :param request: The incoming HTTP request.
    :type request: Request
    :param skip: The number of contacts to skip for pagination.
    :type skip: int
    :param limit: The maximum number of contacts to return for pagination.
    :type limit: int
    :param db: The database session.
    :type db: Session
    :param current_user: The currently authenticated user.
    :type current_user: User
    :param first_name: Optional filter for the contact's first name (supports partial matching).
    :type first_name: str, optional
    :param last_name: Optional filter for the contact's last name (supports partial matching).
    :type last_name: str, optional
    :param email: Optional filter for the contact's email (supports partial matching).
    :type email: str, optional
    :raises HTTPException: If the rate limit of 10 requests per minute is exceeded.
    :return: A list of contacts matching the specified criteria.
    :rtype: List[ContactResponse]
    """
    print(f"Searching for contacts: current_user={current_user.email} first_name={first_name}, last_name={last_name}, email={email}")
    # Використовуємо або пошук, або просто повертаємо контакти
    contacts = await repository_contacts.get_contacts(db, current_user, first_name, last_name, email)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def read_contact(contact_id: int, db: Session = Depends(get_db),
                       current_user: User = Depends(auth_service.get_current_user)):
    """
    Retrieves a single contact by its ID for the authenticated user.

    :http method: GET
    :path: /{contact_id}
    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param db: The database session.
    :type db: Session
    :param current_user: The currently authenticated user.
    :type current_user: User
    :raises HTTPException: If the contact with the specified ID is not found.
    :return: The contact with the specified ID.
    :rtype: ContactResponse
    """
    contact = await repository_contacts.read_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contact {contact_id} not found")
    return contact


@router.post("/", response_model=ContactResponse, description='No more than 5 new contacts per minute',
             dependencies=[Depends(RateLimiter(times=5, seconds=60))], status_code=status.HTTP_201_CREATED,
             responses={201: {"description": "Contact created", "model": ContactResponse}})
async def create_contact(request: Request,
                         body: ContactBase, 
                         db: Session = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):  # Додаємо параметр request для того, щоб уникнути проблем при розпаковці отриманих даних в тестах pytest
    """
    Creates a new contact record in the database for the authenticated user.

    :http method: POST
    :path: /
    :param body: The data required to create a new contact.
    :type body: ContactBase
    :param db: The database session.
    :type db: Session
    :param current_user: The currently authenticated user.
    :type current_user: User
    :raises HTTPException: If the rate limit of 5 requests per minute is exceeded.
    :param request: The incoming HTTP request.
    :type request: Request
    :return: The newly created contact.
    :rtype: ContactResponse
    """
    new_contact = await repository_contacts.create_contact(body, current_user, db)
    return ContactResponse.from_orm(new_contact)


@router.put("/{contact_id}", response_model=ContactResponse) # All fields must be provided when updating a contact
async def update_contact(contact_id: int, body: ContactUpdate, db: Session = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
    """
    Updates a contact by its ID for the authenticated user. All fields must be filled when updating.

    :http method: PUT
    :path: /{contact_id}
    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param body: The data required to update a contact.
    :type body: ContactUpdate
    :param db: The database session.
    :type db: Session
    :param current_user: The currently authenticated user.
    :type current_user: User
    :raises HTTPException: If the contact with the specified ID is not found.
    :return: The updated contact.
    :rtype: ContactResponse
    """
    contact = await repository_contacts.update_contact(contact_id, body, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", response_model=ContactResponse)
async def remove_contact(contact_id: int, db: Session = Depends(get_db),
                      current_user: User = Depends(auth_service.get_current_user)):
    """
    Deletes a contact by its ID for the authenticated user. 

    :http method: DELETE
    :path: /{contact_id}
    :param contact_id: The ID of the contact to delete.
    :type contact_id: int
    :param db: The database session.
    :type db: Session
    :param current_user: The currently authenticated user.
    :type current_user: User
    :raises HTTPException: If the contact with the specified ID is not found.
    :return: The deleted contact.
    :rtype: ContactResponse
    """
    contact = await repository_contacts.remove_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact




