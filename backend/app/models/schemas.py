from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NovelBase(BaseModel):
    title: str

class NovelCreate(NovelBase):
    pass

class Novel(NovelBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    role: str
    content: str
    novel_id: int

class Message(MessageCreate):
    id: int

    class Config:
        from_attributes = True

class PromptButtonBase(BaseModel):
    name: str
    type: str
    content: str
    category: str

class PromptButtonCreate(PromptButtonBase):
    pass

class PromptButton(PromptButtonBase):
    id: int

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    novel_id: int
    messages: list
    prompt_buttons: Optional[list] = None
    model_config_id: Optional[int] = None
    reasoning_effort: Optional[str] = None
    thinking: Optional[dict] = None