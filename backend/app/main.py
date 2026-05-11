from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat, novels, model_configs, settings
from app.models.database import create_tables, init_default_model_configs

app = FastAPI(title="ChatWithMe API")

# Initialize database tables and default configs
create_tables()
init_default_model_configs()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(novels.router, prefix="/api")
app.include_router(model_configs.router, prefix="/api")
app.include_router(settings.router, prefix="/api")

@app.get("/api/health")
def health():
    return {"status": "ok"}