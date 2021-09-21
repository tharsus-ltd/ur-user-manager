import json
import uuid

from typing import Optional
from datetime import timedelta, datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
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
    new_user = UserInDB(
        username=username,
        hashed_password=get_password_hash(password)
    )
    await Handlers().redis.set(get_key(username), new_user.json())
    return new_user


async def get_user(username: Optional[str]) -> UserInDB:
    if Handlers().redis.exists(get_key(username)):
        raw = await Handlers().redis.get(get_key(username))
        user_dict = json.loads(raw)
        return UserInDB(**user_dict)
    raise ValueError(f"Username: {username} not found")


async def authenticate_user(username: str, password: str) -> UserInDB:
    user = await get_user(username)
    if not user:
        raise ValueError(f"Error getting user: {username}")
    if not verify_password(password, user.hashed_password):
        raise ValueError(f"Error verifying password for username: {username}")
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({
        "iss": __service__.replace(" ", "-").lower(),
        "exp": expire,
        "iat": datetime.utcnow(),
        "aud": ["all"],
        "jti": str(uuid.uuid4())
    })
    encoded_jwt = jwt.encode(to_encode, __secret_key__, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, __secret_key__, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = await get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return User(**user.dict())


async def get_user_from_token(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, __secret_key__, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = await get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return User(**user.dict())


async def get_active_user(user: User = Depends(get_user_from_token)):
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
