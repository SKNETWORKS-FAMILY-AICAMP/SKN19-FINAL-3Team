from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # 1. 이거 임포트 필수
from app.api.routes import router
from common.core.config import settings

app = FastAPI(title="AJC Knowledge System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS, 
    allow_credentials=True,
    allow_methods=["*"],    # GET, POST 등 모든 방식 허용
    allow_headers=["*"],    # 모든 헤더 허용
)

app.include_router(router, prefix="/api/v1", tags=["v1"])

@app.get("/health")
def health():
    return {"status": "ok"}