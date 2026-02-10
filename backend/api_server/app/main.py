from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware # 1. 이거 임포트 필수
from app.api.documents import router as document_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.admin import admin_router
from app.api.dependencies import get_current_user
from common.core.config import settings

app = FastAPI(title="AJC Knowledge System")

@app.on_event("startup")
async def startup_event():
    # [Validation] API Server 필수 환경 변수 체크
    if not settings.JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY is missing in .env or environment")
    if not settings.ACCESS_TOKEN_EXPIRE_MINUTES:
        raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES is missing")
    if not settings.AES_SECRET_KEY:
        raise ValueError("AES_SECRET_KEY is missing (required for CryptoService)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS, 
    allow_credentials=True,
    allow_methods=["*"],    # GET, POST 등 모든 방식 허용
    allow_headers=["*"],    # 모든 헤더 허용
)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])  # Public for registration (or protect if needed)
app.include_router(document_router, prefix="/api/v1", tags=["documents"], dependencies=[Depends(get_current_user)])
app.include_router(admin_router, prefix="/api/v1", tags=["admin"], dependencies=[Depends(get_current_user)])

@app.get("/health")
def health():
    return {"status": "ok"}