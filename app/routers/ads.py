from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.backend.db_depends import get_db
from app.models.ads import Ad
from app.models.users import User
from app.schemas import ModelAd, CreateAd, UpdateAd

router = APIRouter()


# ADS
# 1.	Объявления все открытый GET	http://127.0.0.1:8000/api/ads/
@router.get("/ads/")
async def all_ads(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    ads = db.execute(select(Ad).offset(skip).limit(limit)).scalars().all()
    return ads


# 2.	Объявление id открытый GET	http://127.0.0.1:8000/api/ad/2/
@router.get("/ad/{ad_id}")
async def get_ad(ad_id: int, db: Session = Depends(get_db)):
    ad = db.execute(select(Ad).where(Ad.id == ad_id)).scalar_one_or_none()
    if ad is None:
        raise HTTPException(status_code=404, detail="Ad not found")
    return ad


# 3.	Создать свое закрыт POST	http://127.0.0.1:8000/api/ad/create/
@router.post("/ad/create/", response_model=ModelAd)
async def create_ad(ad_request: CreateAd,
                    current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    new_ad = Ad(title=ad_request.title, category=ad_request.category, price=ad_request.price,
                description=ad_request.description, owner=current_user)
    db.add(new_ad)
    db.commit()
    db.refresh(new_ad)

    return new_ad


# 4.	Изменить свое закрыт PUT	http://127.0.0.1:8000/api/ad/7/update/
@router.put("/ad/{ad_id}/update/", response_model=ModelAd)
async def update_ad(ad_id: int, ad_request: UpdateAd,
                    current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    ad = db.execute(select(Ad).where(Ad.id == ad_id)).scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    if ad.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this ad")
    ad.title = ad_request.title
    ad.category = ad_request.category
    ad.description = ad_request.description
    ad.price = ad_request.price
    db.commit()
    db.refresh(ad)

    return ad


# 5.	Удалить свое закрыт DEL	http://127.0.0.1:8000/api/ad/2/delete/
@router.delete("/ad/{ad_id}/delete/", response_model=dict)
async def delete_ad(ad_id: int,
                    current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    ad = db.execute(select(Ad).where(Ad.id == ad_id)).scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    if ad.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this ad")
    db.delete(ad)
    db.commit()
    return {'message': 'The ad was deleted successfully'}
