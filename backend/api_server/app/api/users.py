from fastapi import APIRouter, Depends, status
from common.schemas import UserCreate, UserResponse
from app.services.user_service import UserService
from app.api.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    service: UserService = Depends(get_user_service)
):
    """
    [User] 사용자 등록 (회원가입)
    - 비밀번호는 암호화(Hashing)되어 저장됨
    """
    return await service.create_user(user_in)
