from datetime import timedelta

from fastapi import Depends, APIRouter, HTTPException
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import (ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, ALGORITHM,
                      REFRESH_TOKEN_EXPIRE_DAYS, create_refresh_token, get_current_user)
from app.backend.db_depends import get_db
from app.config import settings
from app.crud import hash_password, verify_password
from app.models.ads import Ad
from app.models.users import User
from app.schemas import RegisterUser, Token, LoginUser, ModelUser, ModelAd, TokenRequest, UpdateUser

router = APIRouter()


@router.get("/", response_model=dict)
async def welcome():
    return {'message': 'Welcome to board'}


# 1	Пользователи все открыт GET	http://127.0.0.1:8000/api/users/
@router.get("/users/", response_model=list[ModelUser])
async def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.execute(select(User).offset(skip).limit(limit)).scalars().all()
    if users is None:
        raise HTTPException(status_code=404, detail="Users  not found")
    return users


# 2	Объявления пользователя id открыт GET	http://127.0.0.1:8000/api/user/<user_id>/ads/
@router.get("/user/{user_id}/ads/", response_model=list[ModelAd])
async def ads_by_user_id(user_id: int, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    ads = db.execute(select(Ad).where(Ad.user_id == user_id)).scalars().all()
    if not ads:
        raise HTTPException(status_code=404, detail='Ads not found')
    return ads


# 3	Защищённый GET self	http://127.0.0.1:8000/api/user/protected/
@router.get("/user/protected/", response_model=ModelUser)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


# 4	Пользователь id открыт GET	http://127.0.0.1:8000/api/user/<user_id>/
@router.get("/user/{user_id}/", response_model=ModelUser)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User  not found")
    return user


# 5	Изменить свою закрыт PUT	http://127.0.0.1:8000/api/user/update/
@router.put("/user/update/", response_model=ModelUser)
async def update_user_data(user: UpdateUser,
                           current_user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    exist_user = db.execute(select(User).filter(
        (User.username == user.username) | (User.email == user.email))).scalar_one_or_none()

    if exist_user and exist_user.id != current_user.id:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    for key, value in vars(user).items():
        if hasattr(current_user, key):
            setattr(current_user, key, value)
            if key == 'password':
                current_user.password = hash_password(user.password)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return current_user


# 6	Удалить свою закрыт DEL	http://127.0.0.1:8000/api/user/delete/
@router.delete("/user/delete/", status_code=204)
async def delete_user(current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    if not current_user:
        raise HTTPException(status_code=404, detail="User  not found")

    db.delete(current_user)
    db.commit()


# 7	Регистрация открыт POST	http://127.0.0.1:8000/api/user/register/
@router.post("/user/register/")
async def register_user(username: RegisterUser, db: Session = Depends(get_db)):
    exist_user = db.execute(select(User).filter(
        (User.username == username.username) | (User.email == username.email))).scalar_one_or_none()

    if exist_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    new_user = User(username=username.username, password=hash_password(username.password),
                    email=username.email, first_name=username.first_name, last_name=username.last_name,
                    phone=username.phone)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "user_id": new_user.id}



# 8	Авторизация открыт POST	http://127.0.0.1:8000/api/token/login/
@router.post("/token/login/", response_model=dict)
async def login(username: LoginUser, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.username == username.username)).scalar_one_or_none()
    if user is None or not verify_password(username.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data={"sub": user.username}, expires_delta=refresh_token_expires)

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


# 9	Рефреш-токен закрыт POST	http://127.0.0.1:8000/api/token/refresh/
@router.post("/token/refresh/", response_model=Token)
async def refresh_token(token_request: TokenRequest, db: Session = Depends(get_db)):
    refresh_token = token_request.refresh_token
    credentials_exception = HTTPException(status_code=401, detail="Invalid refresh token")
    try:
        payload = jwt.decode(refresh_token, settings.refresh_secret_key, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(data={"sub": username}, expires_delta=access_token_expires)
    new_refresh_token = create_refresh_token(data={"sub": username}, expires_delta=refresh_token_expires)

    return {"access_token": access_token, "token_type": "bearer", "refresh_token": new_refresh_token}
