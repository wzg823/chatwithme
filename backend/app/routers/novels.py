from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import Novel, Message, NovelFlows
from app.models.schemas import Novel as NovelSchema, NovelCreate
from pydantic import BaseModel
from datetime import datetime
import json

router = APIRouter()

class MessageCreate(BaseModel):
    role: str
    content: str

class MessageSchema(BaseModel):
    id: int
    role: str
    content: str
    novel_id: int
    flow_type: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True

class NovelFlowsSchema(BaseModel):
    id: int
    novel_id: int
    name: str
    prompt: str | None = None
    enabled: bool = True
    created_at: datetime | None = None

    class Config:
        from_attributes = True

class NovelFlowsCreate(BaseModel):
    name: str
    prompt: str | None = None
    from_template: str | None = None

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

@router.put("/novels/{novel_id}", response_model=NovelSchema)
def update_novel(novel_id: int, novel: NovelCreate, db: Session = Depends(get_db)):
    db_novel = db.query(Novel).filter(Novel.id == novel_id).first()
    if not db_novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    db_novel.title = novel.title
    db.commit()
    db.refresh(db_novel)
    return db_novel

@router.delete("/novels/{novel_id}")
def delete_novel(novel_id: int, db: Session = Depends(get_db)):
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    db.delete(novel)
    db.commit()
    return {"deleted": True}

@router.get("/novels/{novel_id}/messages", response_model=list[MessageSchema])
def get_novel_messages(novel_id: int, flow_type: str = None, db: Session = Depends(get_db)):
    query = db.query(Message).filter(Message.novel_id == novel_id)
    if flow_type:
        query = query.filter(Message.flow_type == flow_type)
    else:
        # 默认获取 null（兼容旧数据）
        query = query.filter(Message.flow_type == None)
    return query.all()

@router.post("/novels/{novel_id}/messages", response_model=MessageSchema)
def create_novel_message(novel_id: int, message: MessageCreate, flow_type: str = None, db: Session = Depends(get_db)):
    msg = Message(role=message.role, content=message.content, novel_id=novel_id, flow_type=flow_type)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

# ========== Novel Flows API ==========

@router.get("/novels/{novel_id}/flows", response_model=list[NovelFlowsSchema])
def get_novel_flows(novel_id: int, db: Session = Depends(get_db)):
    """获取小说的所有流程配置"""
    return db.query(NovelFlows).filter(NovelFlows.novel_id == novel_id).all()

@router.post("/novels/{novel_id}/flows", response_model=NovelFlowsSchema)
def create_novel_flow(novel_id: int, flow: NovelFlowsCreate, db: Session = Depends(get_db)):
    """为小说创建新流程"""
    # 如果指定了 from_template，从系统预设复制
    name = flow.name
    prompt = flow.prompt or ""
    if flow.from_template:
        from app.models.models import ModelConfig
        config = db.query(ModelConfig).first()
        if config and config.prompt_templates:
            try:
                obj = json.loads(config.prompt_templates)
                writing_flows = obj.get("writing_flows", [])
                template = next((f for f in writing_flows if f["id"] == flow.from_template), None)
                if template:
                    name = template.get("name", flow.name)
                    prompt = template.get("prompt", "")
            except (json.JSONDecodeError, AttributeError):
                pass

    db_flow = NovelFlows(
        novel_id=novel_id,
        name=name,
        prompt=prompt,
        enabled=True
    )
    db.add(db_flow)
    db.commit()
    db.refresh(db_flow)
    return db_flow

@router.delete("/novels/{novel_id}/flows/{flow_id}")
def delete_novel_flow(novel_id: int, flow_id: int, db: Session = Depends(get_db)):
    """删除小说的流程"""
    flow = db.query(NovelFlows).filter(NovelFlows.id == flow_id, NovelFlows.novel_id == novel_id).first()
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    db.delete(flow)
    db.commit()
    return {"deleted": True}