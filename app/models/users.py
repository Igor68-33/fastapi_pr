from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.backend.db import Base


# Модель User
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, nullable=False, unique=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # Хранится хэш пароля
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    ads = relationship("Ad", back_populates="owner")  # Связь с объявлениями
