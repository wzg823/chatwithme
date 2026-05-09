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

    flow_type = request.flow_type

    # 按 flow_type 过滤加载历史消息
    query = db.query(Message).filter(Message.novel_id == request.novel_id)
    if flow_type:
        query = query.filter(Message.flow_type == flow_type)
    else:
        query = query.filter(Message.flow_type == None)

    history_messages = query.all()
    messages = [{"role": m.role, "content": m.content} for m in history_messages]

    if request.messages:
        for user_msg in request.messages:
            msg = Message(
                role=user_msg["role"],
                content=user_msg["content"],
                novel_id=novel.id,
                flow_type=flow_type
            )
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

    response = adapter.stream_message(messages, {"temperature": model_config.temperature, "max_tokens": model_config.max_tokens})
    return StreamingResponse(response, media_type="text/event-stream")
