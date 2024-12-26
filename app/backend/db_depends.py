from app.backend.db import SessionLocal


# Получение сессии бд
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
