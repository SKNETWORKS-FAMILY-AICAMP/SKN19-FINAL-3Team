"""
사용법 참고:

dependencies 모듈은 FastAPI Depends로 객체를 생성·주입하는 조립소 역할만 한다.
Router는 여기서 준비된 Service/Repository를 받아 사용하고, 비즈니스 로직은 이곳에 두지 않는다.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

# -----------------------------------------------------------------------------
# Core & Config
# -----------------------------------------------------------------------------
from common.core.database import get_db
from common.core.config import settings
from common.core.crypto import CryptoService
from common.schemas import TokenData
from common.models import User

# -----------------------------------------------------------------------------
# Repositories (Layer 1) - DB 접근 주체
# -----------------------------------------------------------------------------
from common.repositories.section_repo import SectionRepository as SctRepo
from common.repositories.redis_repo import RedisRepository as RdsRepo
from common.repositories.common_code_repo import CommonCodeRepository as CCRepo
from common.repositories.model_logs_repo import ModelLogsRepository as LogRepo
from common.repositories.doc_recipes_repo import DocRecipesRepository as RecipeRepo
from common.repositories.original_texts_repo import OriginalTextsRepository as OrigTextRepo
from common.repositories.secure_token_repo import SecureTokenRepository as TokenRepo
from common.repositories.section_recipes_repo import SectionRecipesRepository as SectRecipeRepo
from common.repositories.mixed_repo import MixedRepository as MixedRepo
from common.repositories.user_repo import UserRepository
from common.repositories.team_repo import TeamRepository as TeamRepo
from common.repositories.local_repo import DocLocalRepository as LocalRepo
from common.util.search_word import DocSearch as SearchEngine
from common.repositories.pattern_repo import PatternRepository
from common.repositories.tag_repo import TagRepository
from common.repositories.doc_permission_repo import DocPermissionRepository

# -----------------------------------------------------------------------------
# Services (Layer 2) - 비즈니스 로직
# -----------------------------------------------------------------------------
from app.services.document_adaption import DocumentAdaptionService as DocSvc
from app.services.common_code_service import CommonCodeService as CCSrvc
from app.services.admin_service import AdminService as AdminSvc

# =================================================================
# [Dependency Injection - Repository]
# FastAPI의 Depends를 사용하여 객체 생성과 주입을 자동화함.
# =================================================================

def get_redis_repo() -> RdsRepo:
    return RdsRepo(settings.REDIS_URL)

def get_common_code_repo(db: AsyncSession = Depends(get_db)) -> CCRepo:
    return CCRepo(db)

def get_model_logs_repo(db: AsyncSession = Depends(get_db)) -> LogRepo:
    return LogRepo(db)

def get_model_recipe_repo(db: AsyncSession = Depends(get_db)) -> RecipeRepo:
    return RecipeRepo(db)

def get_model_sct_repo(db: AsyncSession = Depends(get_db)) -> SctRepo:
    return SctRepo(db)

def get_model_text_repo(db: AsyncSession = Depends(get_db)) -> OrigTextRepo:
    return OrigTextRepo(db)

def get_secure_token_repo(db: AsyncSession = Depends(get_db)) -> TokenRepo:
    return TokenRepo(db)

def get_model_section_recipe_repo(db: AsyncSession = Depends(get_db)) -> SectRecipeRepo:
    return SectRecipeRepo(db)

def get_mixed_repo(db: AsyncSession = Depends(get_db)) -> MixedRepo:
    return MixedRepo(db)

def get_local_repo(db: AsyncSession = Depends(get_db)) -> LocalRepo:
    return LocalRepo(db)

def get_search_engine(db: AsyncSession = Depends(get_db)) -> SearchEngine:
    return SearchEngine(db)
    
def get_pattern_repo(db: AsyncSession = Depends(get_db)) -> PatternRepository:
    return PatternRepository(db)

def get_doc_permission_repo(db: AsyncSession = Depends(get_db)) -> DocPermissionRepository:
    return DocPermissionRepository(db)

def get_tag_repo(db: AsyncSession = Depends(get_db)) -> TagRepository:
    return TagRepository(db)

def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

# =================================================================
# [Dependency Injection - Auth]
# =================================================================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = CryptoService.decode_jwt(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
        
    user_repo = UserRepository(db)
    user = await user_repo.get_by_username(token_data.username)
    if user is None:
        raise credentials_exception
    return user


# =================================================================
# [Dependency Injection - Service]
# Router는 복잡한 초기화 과정 없이 완성된 Service 객체만 받아 사용함.
# =================================================================

# ---------------------- Common Code ----------------------
def get_common_code_service(repo: CCRepo = Depends(get_common_code_repo)) -> CCSrvc:
    return CCSrvc(repo)

# ---------------------- Document Adaption ----------------------
def get_document_adaption_service(
    redis_repo: RdsRepo = Depends(get_redis_repo),
    logs_repo: LogRepo = Depends(get_model_logs_repo),
    sct_repo: SctRepo = Depends(get_model_sct_repo),
    recipe_repo: RecipeRepo = Depends(get_model_recipe_repo),
    text_repo: OrigTextRepo = Depends(get_model_text_repo),
    token_repo: TokenRepo = Depends(get_secure_token_repo),
    mixed_repo: MixedRepo = Depends(get_mixed_repo),
    section_recipe_repo: SectRecipeRepo = Depends(get_model_section_recipe_repo),
    user: User = Depends(get_current_user),
    local_repo: LocalRepo = Depends(get_local_repo),
    search_engine: SearchEngine = Depends(get_search_engine),
    pattern_repo: PatternRepository = Depends(get_pattern_repo)
) -> DocSvc:
    return DocSvc(
        redis_repo=redis_repo, 
        logs_repo=logs_repo, 
        sct_repo=sct_repo, 
        recipe_repo=recipe_repo, 
        text_repo=text_repo,
        token_repo=token_repo,
        mixed_repo=mixed_repo,
        section_recipe_repo=section_recipe_repo,
        user=user,
        local_repo=local_repo,
        search_engine=search_engine,
        pattern_repo=pattern_repo
    )

#---------------------- Admin ----------------------
def get_admin_service(
    pattern_repo: PatternRepository = Depends(get_pattern_repo),
    doc_permission_repo: DocPermissionRepository = Depends(get_doc_permission_repo),
    tag_repo: TagRepository = Depends(get_tag_repo),
    audit_log_repo: LogRepo = Depends(get_model_logs_repo),
    user_repo: UserRepository = Depends(get_user_repo)
) -> AdminSvc:
    return AdminSvc(
        pattern_repo=pattern_repo,
        doc_permission_repo=doc_permission_repo,
        tag_repo=tag_repo,
        audit_log_repo=audit_log_repo,
        user_repo=user_repo
    )