import logging
from datetime import timedelta

from fastapi import Depends, APIRouter, HTTPException
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette import status

from app.auth import (ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, ALGORITHM,
                      REFRESH_TOKEN_EXPIRE_DAYS, create_refresh_token, REFRESH_SECRET_KEY, get_current_user)
from app.backend.db_depends import get_db
from app.crud import hash_password, verify_password
from app.models.ads import Ad
from app.models.users import User
from app.schemas import RegisterUser, Token, LoginUser, ModelUser, ModelAd

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


# 1.	Пользователи все открыт GET	http://127.0.0.1:8000/api/users/
@router.get("/users", response_model=list[ModelUser])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.execute(select(User).offset(skip).limit(limit)).scalars().all()
    return users


# 2.	Пользователь id открыт GET	http://127.0.0.1:8000/api/user/<user_id>
@router.get("/user/{user_id}", response_model=ModelUser)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User  not found")
    return user


# 3.	Объявления пользователя id открыт GET	http://127.0.0.1:8000/api/user/2/advs/
@router.get("/user/{user_id}/advs", response_model=list[ModelAd])
def ads_by_user_id(user_id: int, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    ads = db.execute(select(Ad).where(Ad.user_id == user_id)).scalars().all()
    if not ads:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Ads were not found'
        )
    return ads


# 4.	Регистрация открыт POST	http://127.0.0.1:8000/api/user/register/
@router.post("/user/register")
def register_user(username: RegisterUser, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.username == username.username)).scalar_one_or_none()
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = User(username=username.username, password=hash_password(username.password),
                    email=username.email, first_name=username.first_name, last_name=username.last_name,
                    phone=username.phone)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "user_id": new_user.id}


# 5.	Авторизация открыт POST	http://127.0.0.1:8000/api/token/login/
@router.post("/token/login", response_model=Token)
def login(username: LoginUser, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.username == username.username)).scalar_one_or_none()
    if not user or not verify_password(username.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data={"sub": user.username}, expires_delta=refresh_token_expires)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# 6.	Рефреш-токен закрыт POST	http://127.0.0.1:8000/api/token/refresh/
@router.post("/token/refresh", response_model=Token)
def refresh_tokens(refresh_token: str, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Invalid refresh token")
    try:
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User  not found")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(data={"sub": username}, expires_delta=access_token_expires)
    new_refresh_token = create_refresh_token(data={"sub": username}, expires_delta=refresh_token_expires)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token
    }


# 7.	Изменить свою закрыт PUT	http://127.0.0.1:8000/api/user/<user_id>
@router.put("/user/{user_id}", response_model=dict)
def update_user_data(user_id: int, user: ModelUser, current_user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this user")
    #  замена заполненных полей
    for key, value in vars(current_user).items():
        if hasattr(user, key):
            setattr(user, key, value)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return {"message": "User data updated successfully"}


# # 7.	Изменить свою закрыт PUT	http://127.0.0.1:8000/api/user/<user_id>
# @router.put("/user/{user_id}", response_model=dict)
# def update_user_data(current_user: ModelUser, user=Depends(get_current_user), db: Session = Depends(get_db)):
#
#     # for key, value in vars(current_user).items():
#     #     if hasattr(user, key):
#     #         setattr(user, key, value)
#
#     db.add(current_user)
#     db.commit()
#     db.refresh(current_user)
#
#     return {"message": "User data updated successfully"}


# 8.	Удалить свою закрыт DEL	http://127.0.0.1:8000/api/user/<user_id>
@router.delete("/user/{user_id: int}", response_model=dict)
def delete_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this user")
    db.delete(current_user)
    db.commit()
    return {"message": "deleted"}


# 9.	Защищённый GET	http://127.0.0.1:8000/api/user/protected/
@router.get("/user/protected", response_model=ModelUser)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
