import redis.asyncio as redis
from fastapi import FastAPI, Depends
from fastapi_limiter import FastAPILimiter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse # для обсл.favicon.ico

from src.routes import contacts, auth, users
from src.conf.config import settings

app = FastAPI()

# щоб не випадало повідомлення "GET /favicon.ico HTTP/1.1" 404 Not Found:
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """
    Serves the favicon.ico file.

    This endpoint ensures that requests for the favicon do not result in a 404 error.

    :return: The favicon.ico file as a response.
    :rtype: FileResponse
    """
    return FileResponse("favicon.ico")

# Визначаємо список дозволених джерел
origins = [ 
    "http://localhost:3000"
    ]

# Додаємо CORSMiddleware у застосунок
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix='/api')
app.include_router(contacts.router, prefix='/api') 
app.include_router(users.router, prefix='/api')

@app.on_event("startup")
async def startup():
    """
    Initializes the application on startup.

    Connects to the Redis database and configures the FastAPILimiter for rate limiting.

    :raises redis.exceptions.ConnectionError: If there is an issue connecting to Redis.
    """
    print("Attempting to connect to Redis...")
    r = await redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0, encoding="utf-8",
                          decode_responses=True)
    print("Redis connection established.")
    await FastAPILimiter.init(r)
    print("FastAPILimiter initialized.")


@app.get("/") 
async def root():
    """
    Root endpoint of the application.

    Provides a welcome message for users visiting the base URL. 
    Available 2 times per 5 second as limit maximum.

    :return: A dictionary with a welcome message.
    :rtype: dict
    """
    return {"message": "Welcome to my Fast API web-application!"}