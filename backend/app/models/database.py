from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

os.makedirs("data", exist_ok=True)

SQLALCHEMY_DATABASE_URL = "sqlite:///./data/chatwithme.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Import all models to register them with Base
from app.models.models import Novel, Message, WorldSetting, Outline, Chapter, PlotThread, PromptCategory, PromptButton, ModelConfig, NovelFlows

def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully")

def init_default_model_configs():
    """初始化默认模型配置"""
    from app.models.models import ModelConfig as ModelConfigModel

    session = SessionLocal()
    try:
        existing = session.query(ModelConfigModel).count()
        if existing > 0:
            print(f"Model configs already exist ({existing}), skipping init")
            return

        configs = [
            ModelConfigModel(
                provider="openai",
                base_url="https://api.openai.com/v1",
                model="gpt-4",
                temperature=0.7,
                max_tokens=4096
            ),
            ModelConfigModel(
                provider="deepseek",
                base_url="https://api.deepseek.com",
                model="deepseek-v4-flash",
                temperature=0.7,
                max_tokens=4096
            ),
            ModelConfigModel(
                provider="deepseek",
                base_url="https://api.deepseek.com",
                model="deepseek-v4-pro",
                temperature=0.7,
                max_tokens=4096
            ),
            ModelConfigModel(
                provider="deepseek",
                base_url="https://api.deepseek.com",
                model="deepseek-reasoner",
                temperature=0.7,
                max_tokens=4096
            ),
        ]
        for config in configs:
            session.add(config)
        session.commit()
        print(f"Initialized {len(configs)} default model configs")
    finally:
        session.close()