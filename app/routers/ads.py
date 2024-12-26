from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.backend.db_depends import get_db
from app.models.ads import Ad
from app.models.users import User
from app.schemas import ModelAd, CreateAd, UpdateAd

router = APIRouter()

# ADS
# 1.	Объявления все открытый GET	http://127.0.0.1:8000/api/advs/
@router.get("/advs")
def all_ads(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    ads = db.execute(select(Ad).offset(skip).limit(limit)).scalars().all()
    return ads


# 2.	Объявление id открытый GET	http://127.0.0.1:8000/api/adv/2/
@router.get("/adv/{ad_id}")
def get_ad(ad_id: int, db: Session = Depends(get_db)):
    ad = db.execute(select(Ad).where(Ad.id == ad_id)).scalar_one_or_none()
    if ad is None:
        raise HTTPException(status_code=404, detail="Ad not found")
    return ad

# 3.	Объявления пользователя id открыт GET	http://127.0.0.1:8000/api/user/2/adv/



# 4.	Создать свое закрыт POST	http://127.0.0.1:8000/api/adv/
@router.post("/adv/", response_model=ModelAd)
def create_ad(ad_request: CreateAd, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.id == ad_request.user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User  not found")

    new_ad = Ad(title=ad_request.title, category=ad_request.category, price=ad_request.price,
                description=ad_request.description, owner=user)
    db.add(new_ad)
    db.commit()
    db.refresh(new_ad)

    return new_ad

# 5.	Изменить свое закрыт PUT	http://127.0.0.1:8000/api/adv/7/
@router.put("/adv/{ad_id}", response_model=ModelAd)
def update_ad(ad_id: int, ad_request: UpdateAd, db: Session = Depends(get_db)):
    ad = db.execute(select(Ad).where(Ad.id == ad_id)).scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    user = db.execute(select(User).where(User.id == ad_request.user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User  not found")
    ad.title = ad_request.title
    ad.category = ad_request.category
    ad.description = ad_request.description
    ad.price = ad_request.price
    db.commit()
    db.refresh(ad)

    return ad

# 6.	Удалить свое закрыт DEL	http://127.0.0.1:8000/api/adv/2/
@router.delete("/adv/{ad_id}", status_code=204)
def delete_ad(ad_id: int, user_id: int, db: Session = Depends(get_db)):
    ad = db.execute(select(Ad).where(Ad.id == ad_id)).scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    if ad.user_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this ad")
    db.delete(ad)
    db.commit()
    return
