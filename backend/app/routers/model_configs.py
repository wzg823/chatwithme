from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import ModelConfig, UserModelPreference
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ModelConfigCreate(BaseModel):
    provider: str
    base_url: Optional[str] = None
    model: str
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096

class ModelConfigResponse(ModelConfigCreate):
    id: int

    class Config:
        from_attributes = True

class UserModelPreferenceCreate(BaseModel):
    user_id: Optional[int] = None
    model_config_id: int
    is_default: bool = True

class UserModelPreferenceResponse(BaseModel):
    id: int
    user_id: Optional[int]
    model_config_id: int
    is_default: bool

    class Config:
        from_attributes = True

@router.get("/model-configs", response_model=list[ModelConfigResponse])
def list_model_configs(db: Session = Depends(get_db)):
    return db.query(ModelConfig).all()

@router.post("/model-configs", response_model=ModelConfigResponse)
def create_model_config(config: ModelConfigCreate, db: Session = Depends(get_db)):
    try:
        db_config = ModelConfig(**config.model_dump(exclude_none=True))
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        return db_config
    except Exception:
        db.rollback()
        raise

@router.get("/user-model-preferences", response_model=list[UserModelPreferenceResponse])
def list_user_model_preferences(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(UserModelPreference)
    if user_id is not None:
        query = query.filter(UserModelPreference.user_id == user_id)
    return query.all()

@router.post("/user-model-preferences", response_model=UserModelPreferenceResponse)
def create_user_model_preference(pref: UserModelPreferenceCreate, db: Session = Depends(get_db)):
    # 验证 model_config_id 存在
    if not db.get(ModelConfig, pref.model_config_id):
        raise HTTPException(status_code=404, detail="ModelConfig not found")

    try:
        # 如果设置默认，先清除其他默认
        if pref.is_default:
            db.query(UserModelPreference).filter(
                UserModelPreference.user_id == pref.user_id,
                UserModelPreference.is_default == True
            ).update({"is_default": False})

        db_pref = UserModelPreference(**pref.model_dump())
        db.add(db_pref)
        db.commit()
        db.refresh(db_pref)
        return db_pref
    except Exception:
        db.rollback()
        raise

@router.delete("/model-configs/{config_id}")
def delete_model_config(config_id: int, db: Session = Depends(get_db)):
    config = db.get(ModelConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="ModelConfig not found")
    db.delete(config)
    db.commit()
    return {"deleted": True}

@router.put("/model-configs/{config_id}", response_model=ModelConfigResponse)
def update_model_config(config_id: int, config: ModelConfigCreate, db: Session = Depends(get_db)):
    db_config = db.get(ModelConfig, config_id)
    if not db_config:
        raise HTTPException(status_code=404, detail="ModelConfig not found")
    for key, value in config.model_dump(exclude_none=True).items():
        setattr(db_config, key, value)
    db.commit()
    db.refresh(db_config)
    return db_config