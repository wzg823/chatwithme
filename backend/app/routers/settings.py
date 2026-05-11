from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import NovelSetting
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()

class NovelSettingSchema(BaseModel):
    id: int
    novel_id: int
    category: str
    sub_category: str
    title: str
    content: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NovelSettingCreate(BaseModel):
    category: str
    sub_category: str
    title: str
    content: str = ""

class NovelSettingUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = ""

@router.get("/novels/{novel_id}/settings", response_model=dict)
def get_novel_settings(novel_id: int, category: str = None, db: Session = Depends(get_db)):
    """获取小说的设定，按 category 和 sub_category 分组"""
    query = db.query(NovelSetting).filter(NovelSetting.novel_id == novel_id)
    if category:
        query = query.filter(NovelSetting.category == category)

    settings = query.all()

    # 按 category -> sub_category 分组
    result = {}
    for s in settings:
        cat = s.category
        sub = s.sub_category
        if cat not in result:
            result[cat] = {}
        if sub not in result[cat]:
            result[cat][sub] = []
        result[cat][sub].append({
            "id": s.id,
            "novel_id": s.novel_id,
            "category": s.category,
            "sub_category": s.sub_category,
            "title": s.title,
            "content": s.content or "",
            "created_at": s.created_at,
            "updated_at": s.updated_at
        })

    return result

@router.post("/novels/{novel_id}/settings", response_model=NovelSettingSchema)
def create_novel_setting(novel_id: int, setting: NovelSettingCreate, db: Session = Depends(get_db)):
    """创建新设定"""
    db_setting = NovelSetting(
        novel_id=novel_id,
        category=setting.category,
        sub_category=setting.sub_category,
        title=setting.title,
        content=setting.content or ""
    )
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

@router.put("/novels/{novel_id}/settings/{setting_id}", response_model=NovelSettingSchema)
def update_novel_setting(novel_id: int, setting_id: int, setting: NovelSettingUpdate, db: Session = Depends(get_db)):
    """更新设定"""
    db_setting = db.query(NovelSetting).filter(NovelSetting.id == setting_id, NovelSetting.novel_id == novel_id).first()
    if not db_setting:
        raise HTTPException(status_code=404, detail="Setting not found")

    if setting.title is not None:
        db_setting.title = setting.title
    if setting.content is not None:
        db_setting.content = setting.content

    db.commit()
    db.refresh(db_setting)
    return db_setting

@router.delete("/novels/{novel_id}/settings/{setting_id}")
def delete_novel_setting(novel_id: int, setting_id: int, db: Session = Depends(get_db)):
    """删除设定"""
    db_setting = db.query(NovelSetting).filter(NovelSetting.id == setting_id, NovelSetting.novel_id == novel_id).first()
    if not db_setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    db.delete(db_setting)
    db.commit()
    return {"deleted": True}