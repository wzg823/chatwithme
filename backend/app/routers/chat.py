from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import Message, Novel, ModelConfig, UserModelPreference
from app.models.schemas import ChatRequest

router = APIRouter()

def get_adapter(model_config: ModelConfig):
    if model_config.provider in ("openai", "deepseek"):
        from app.adapters.openai import OpenAIAdapter
        return OpenAIAdapter(
            api_key=model_config.api_key or "dummy",
            base_url=model_config.base_url,
            model=model_config.model
        )
    return None

@router.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    novel = db.query(Novel).filter(Novel.id == request.novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    messages = [{"role": m.role, "content": m.content} for m in novel.messages]
    if request.messages:
        for user_msg in request.messages:
            msg = Message(role=user_msg["role"], content=user_msg["content"], novel_id=novel.id)
            db.add(msg)
            messages.append({"role": user_msg["role"], "content": user_msg["content"]})
    db.commit()

    # Get model config: request -> user preference -> default
    model_config = None
    if request.model_config_id:
        model_config = db.query(ModelConfig).filter(ModelConfig.id == request.model_config_id).first()

    if not model_config:
        pref = db.query(UserModelPreference).filter(UserModelPreference.is_default == True).first()
        if pref:
            model_config = db.query(ModelConfig).filter(ModelConfig.id == pref.model_config_id).first()

    if not model_config:
        model_config = db.query(ModelConfig).first()

    if not model_config:
        raise HTTPException(status_code=500, detail="No model configuration available")

    adapter = get_adapter(model_config)
    if not adapter:
        raise HTTPException(status_code=500, detail="Unsupported model provider")

    def generate():
        for chunk in adapter.stream_message(messages, {}):
            yield chunk

    return StreamingResponse(generate(), media_type="text/event-stream")

@router.get("/novels/{novel_id}/messages")
def get_messages(novel_id: int, db: Session = Depends(get_db)):
    return db.query(Message).filter(Message.novel_id == novel_id).all()