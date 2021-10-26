import json
import uuid

from typing import Optional
from datetime import timedelta, datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import opentracing
from passlib.context import CryptContext
from jose import JWTError, jwt

from app import __secret_key__, __service__
from app.handlers import Handlers
from app.models import UserInDB, TokenData, User

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_key(username: Optional[str]) -> str:
    return f"user:{username}"


async def set_user(username: str, password: str) -> User:
    with opentracing.tracer.start_active_span("set-user") as scope:
        new_user = UserInDB(
            username=username,
            hashed_password=get_password_hash(password)
        )
        scope.span.log_kv(new_user.dict())
        await Handlers().redis.set(get_key(username), new_user.json())
        return new_user


async def get_user(username: Optional[str]) -> UserInDB:
    with opentracing.tracer.start_active_span("get-user") as scope:
        if await Handlers().redis.exists(get_key(username)):
            raw = await Handlers().redis.get(get_key(username))
            user_dict = json.loads(raw)
            scope.span.log_kv(user_dict)
            return UserInDB(**user_dict)

        err = f"Username: {username} not found"
        scope.span.log_kv({"error": err})
        raise ValueError(err)


async def authenticate_user(username: str, password: str) -> UserInDB:
    with opentracing.tracer.start_active_span("authenticate-user") as scope:
        user = await get_user(username)
        if not user:
            err = f"Error getting user: {username}"
            scope.span.log_kv({"error": err})
            raise ValueError(err)
        if not verify_password(password, user.hashed_password):
            err = f"Error verifying password for username: {username}"
            scope.span.log_kv({"error": err})
            raise ValueError(err)
        return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({
        "iss": get_jwt_issuer(),
        "exp": expire,
        "iat": datetime.utcnow(),
        "aud": ["micro-rocket"],
        "jti": str(uuid.uuid4())
    })
    encoded_jwt = jwt.encode(to_encode, __secret_key__, algorithm=ALGORITHM)
    return encoded_jwt


def get_jwt_issuer() -> str:
    return __service__.replace(" ", "-").lower()


async def user_exists(username: str) -> bool:
    with opentracing.tracer.start_active_span("authenticate-user") as scope:
        res = (await Handlers().redis.exists(get_key(username))) >= 1
        scope.span.log_kv({"result": res})
        return res


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(
            token,
            __secret_key__,
            audience="micro-rocket",
            issuer=get_jwt_issuer(),
            algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username problematic in JWT",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(username=username)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error decoding JWT",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await get_user(username=token_data.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return User(**user.dict())


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
