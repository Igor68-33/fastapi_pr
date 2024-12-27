from datetime import datetime, timezone
from datetime import timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.schemas import LoginUser

# Конфигурация
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_MINUTES = 1440


# Модель пользователя
class User(BaseModel):
    username: str
    email: str
    full_name: str
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


# Модель токена
class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str


# Функции для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


# Имитация базы данных пользователей
fake_users_db = {
    "qwe": {
        "username": "qwe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": get_password_hash("qwe"),
        "disabled": False,
    }
}

# Функции для работы с токенами
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta

    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Проверка токена
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = fake_users_db.get(token_data.username)
    if user is None:
        raise credentials_exception
    return user


# Создание
router = APIRouter()

# Определяем модель для тела запроса
class TokenRequest(BaseModel):
    refresh_token: str

REFRESH_TOKEN_EXPIRE_DAYS=7


@router.post("/token/login", response_model=Token)
async def login(form_data: LoginUser):
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(data={"sub": form_data.username}, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data={"sub": form_data.username}, expires_delta=refresh_token_expires)

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}




@router.post("/token/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user['username']}, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data={"sub": user['username']}, expires_delta=refresh_token_expires)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}









@router.get("/user/protected", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/token/refresh")
async def refresh_token(token_request: TokenRequest):
    refresh_token = token_request.refresh_token

    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token is required")
    # Здесь вы можете добавить логику проверки refresh токена
    # Например, проверка, существует ли он в базе данных
    # Для простоты мы просто создаем новый access токен
    current_user = get_current_user(refresh_token)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": current_user['username']}, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data={"sub": current_user['username']})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


# Модель данных для токена
class TokenData(BaseModel):
    username: str | None = None
