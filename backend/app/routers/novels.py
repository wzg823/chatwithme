from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import Novel
from app.models.schemas import Novel as NovelSchema, NovelCreate

router = APIRouter()

@router.get("/novels", response_model=list[NovelSchema])
def get_novels(db: Session = Depends(get_db)):
    return db.query(Novel).all()

@router.post("/novels", response_model=NovelSchema)
def create_novel(novel: NovelCreate, db: Session = Depends(get_db)):
    db_novel = Novel(title=novel.title)
    db.add(db_novel)
    db.commit()
    db.refresh(db_novel)
    return db_novel

@router.get("/novels/{novel_id}", response_model=NovelSchema)
def get_novel(novel_id: int, db: Session = Depends(get_db)):
    return db.query(Novel).filter(Novel.id == novel_id).first()

@router.delete("/novels/{novel_id}")
def delete_novel(novel_id: int, db: Session = Depends(get_db)):
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    db.delete(novel)
    db.commit()
    return {"deleted": True}