from datetime import datetime

from pydantic import BaseModel, EmailStr


# Модели для запросов
class RegisterUser(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: str


class LoginUser(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class ModelUser(BaseModel):
    id: int
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: str


class UpdateUser(BaseModel):
    username: str
    password: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: str


class ModelAd(BaseModel):
    id : int
    title: str
    category: str
    description: str
    price: float
    created_at: datetime
    updated_at: datetime
    user_id: int


class CreateAd(BaseModel):
    title: str
    category: str
    description: str
    price: float



class UpdateAd(BaseModel):
    title: str
    category: str
    description: str
    price: float



class TokenRequest(BaseModel):
    refresh_token: str
