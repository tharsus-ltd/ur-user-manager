import asyncio
import json

from datetime import timedelta
from typing import List

from jaeger_client import Config
from opentracing.scope_managers.contextvars import ContextVarsScopeManager

from fastapi import FastAPI, status
from fastapi.exceptions import HTTPException
from fastapi.param_functions import Depends
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

from app import JAEGER_HOST, JAEGER_PORT, __root__, __service__, __version__, __startup_time__
from app.handlers import Handlers
from app.models import Token, User
from app.security import (ACCESS_TOKEN_EXPIRE_MINUTES, authenticate_user,
                          create_access_token, get_current_active_user,
                          set_user, user_exists)
from app.tracing import TracingMiddleWare


app = FastAPI(title=__service__, root_path=__root__, version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = Config(
    config={
        'sampler': {
            'type': 'const',
            'param': 1,
        },
        'local_agent': {
            'reporting_host': JAEGER_HOST,
            'reporting_port': JAEGER_PORT,
        },
        'logging': True,
    },
    scope_manager=ContextVarsScopeManager(),
    service_name=__service__,
    validate=True,
)

jaeger_tracer = config.initialize_tracer()
app.add_middleware(TracingMiddleWare, tracer=jaeger_tracer)


@app.on_event("startup")
async def startup():
    # Wait for RabbitMQ and Redis
    await asyncio.sleep(__startup_time__)
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
    if await user_exists(form_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User: {form_data.username} already exists",
        )
    user = await set_user(form_data.username, form_data.password)
    return user


@app.get("/users", response_model=List[User])
async def get_all_users():
    users = []
    async for key in Handlers().redis.scan_iter("user:*"):
        raw = await Handlers().redis.get(key)
        users.append(User(**json.loads(raw)))
    return users


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
