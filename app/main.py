import asyncio

from datetime import timedelta

from fastapi import FastAPI, status
from fastapi.exceptions import HTTPException
from fastapi.param_functions import Depends
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

from app import __root__, __service__, __version__
from app.handlers import Handlers
from app.models import Token, User
from app.security import (ACCESS_TOKEN_EXPIRE_MINUTES, authenticate_user,
                          create_access_token, get_current_active_user,
                          set_user)

app = FastAPI(title=__service__, root_path=__root__, version=__version__)


@app.on_event("startup")
async def startup():
    # Wait for RabbitMQ and Redis
    await asyncio.sleep(20)
    await Handlers().init()


@app.get("/")
async def root():
    return {"Service": __service__, "Version": __version__}


@app.get("/status")
async def get_status():
    # Add checks to ensure the system is running
    return False


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    try:
        user = await authenticate_user(form_data.username, form_data.password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Incorrect username or password: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/register", response_model=User)
async def register_new_user(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await set_user(form_data.username, form_data.password)
    return user


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
