from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from common.core.database import get_db
from common.schemas import UserLogin, Token, UserResponse
from common.models import User
from app.services.user_service import UserService
from app.api.dependencies import get_current_user
router = APIRouter()

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service)
):
    """
    [로그인 API]
    사용자 ID와 비밀번호를 검증하고, Access Token과 Refresh Token을 발급합니다.
    
    - **username**: 로그인 아이디 (OAuth2 표준)
    - **password**: 비밀번호
    - **response**: AccessToken(15분), RefreshToken(7일)
    """
    user_in = UserLogin(username=form_data.username, password=form_data.password)
    user = await service.authenticate_user(user_in)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Device Info from User-Agent
    user_agent = request.headers.get("user-agent", "unknown")
    
    return await service.create_tokens(user, device_info=user_agent)

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    service: UserService = Depends(get_user_service)
):
    """
    [토큰 갱신 API]
    만료된 Access Token을 대신해, 유효한 Refresh Token으로 새로운 Access Token을 발급받습니다.
    
    - **refresh_token**: 이전에 발급받은 Refresh Token 문자열 (Query Parameter)
    - **response**: 새로운 Access Token (기존 Refresh Token은 재사용 또는 로직에 따라 갱신)
    """
    return await service.refresh_access_token(refresh_token)

@router.post("/logout")
async def logout(
    refresh_token: str,
    service: UserService = Depends(get_user_service)
):
    """
    [로그아웃 API]
    서버 DB에 저장된 Refresh Token을 삭제하여 더 이상 갱신이 불가능하도록 만듭니다.
    
    - **refresh_token**: 삭제할 Refresh Token 문자열 (Query Parameter)
    """
    await service.logout(refresh_token)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user)
):
    """
    [토큰 검증 API]
    현재 Access Token이 유효한지 확인하고, 유효하다면 사용자 정보를 반환합니다.
    """
    return current_user


