from sqlalchemy import Column, Float, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.database import Base

class Novel(Base):
    __tablename__ = "novels"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="novel")
    world_settings = relationship("WorldSetting", back_populates="novel")
    outlines = relationship("Outline", back_populates="novel")
    chapters = relationship("Chapter", back_populates="novel")
    plot_threads = relationship("PlotThread", back_populates="novel")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String)
    content = Column(Text)
    novel_id = Column(Integer, ForeignKey("novels.id"))
    flow_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    novel = relationship("Novel", back_populates="messages")

class WorldSetting(Base):
    __tablename__ = "world_settings"
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    novel = relationship("Novel", back_populates="world_settings")

class Outline(Base):
    __tablename__ = "outlines"
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"))
    level = Column(String)
    title = Column(String)
    content = Column(Text)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    novel = relationship("Novel", back_populates="outlines")

class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"))
    number = Column(Integer)
    title = Column(String)
    outline = Column(Text)
    content = Column(Text)
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)

    novel = relationship("Novel", back_populates="chapters")

class PlotThread(Base):
    __tablename__ = "plot_threads"
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"))
    content = Column(Text)
    introduced_chapter = Column(Integer)
    status = Column(String, default="active")
    resolve_chapter = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    novel = relationship("Novel", back_populates="plot_threads")

class PromptCategory(Base):
    __tablename__ = "prompt_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    icon = Column(String, default="📝")
    sort_order = Column(Integer, default=0)

    buttons = relationship("PromptButton", back_populates="category")

class PromptButton(Base):
    __tablename__ = "prompt_buttons"
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("prompt_categories.id"))
    name = Column(String)
    button_type = Column(String)
    content = Column(Text)
    enabled = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    category = relationship("PromptCategory", back_populates="buttons")

class ModelConfig(Base):
    __tablename__ = "model_configs"
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, default="openai")
    base_url = Column(String, nullable=True)
    model = Column(String, default="gpt-4")
    api_key = Column(String, nullable=True)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=4096)
    prompt_templates = Column(Text, nullable=True)  # 新增：存储 JSON 字符串

class UserModelPreference(Base):
    __tablename__ = "user_model_preferences"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    model_config_id = Column(Integer, ForeignKey("model_configs.id"))
    is_default = Column(Boolean, default=False)