"""
사용법 참고:

dependencies 모듈은 FastAPI Depends로 객체를 생성·주입하는 조립소 역할만 한다.
Router는 여기서 준비된 Service/Repository를 받아 사용하고, 비즈니스 로직은 이곳에 두지 않는다.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from common.core.database import get_db
from common.core.config import settings

# 각 계층(Layer)별 클래스 임포트
from common.repositories.section_repo import SectionRepository as SctRepo
from common.repositories.redis_repo import RedisRepository as RdsRepo

from app.services.document_adaption import DocumentAdaptionService as DocSvc
from app.services.common_code_service import CommonCodeService as CCSrvc

from common.repositories.common_code_repo import CommonCodeRepository as CCRepo
from common.repositories.model_logs_repo import ModelLogsRepository as LogRepo
from common.repositories.doc_recipes_repo import DocRecipesRepository as RecipeRepo
from common.repositories.original_texts_repo import OriginalTextsRepository as OrigTextRepo

# =================================================================
# [Dependency Injection - 의존성 주입 정의]
# FastAPI의 Depends를 사용하여 객체 생성과 주입을 자동화함.
# Router는 복잡한 초기화 과정 없이 완성된 객체만 받아 사용함.
# =================================================================


def get_redis_repo() -> RdsRepo:
    return RdsRepo(settings.REDIS_URL)


# ---------------------- Common Code ----------------------
def get_common_code_repo(db: AsyncSession = Depends(get_db)) -> CCRepo:
    return CCRepo(db)

def get_common_code_service(repo: CCRepo = Depends(get_common_code_repo)) -> CCSrvc:
    return CCSrvc(repo)

def get_model_logs_repo(db: LogRepo = Depends(get_db)) -> LogRepo:
    return LogRepo(db)

def get_model_Recipe_repo(db: RecipeRepo = Depends(get_db)) -> RecipeRepo:
    return RecipeRepo(db)

def get_model_logs_repo(db: LogRepo = Depends(get_db)) -> LogRepo:
    return LogRepo(db)

def get_model_sct_repo(db: SctRepo = Depends(get_db)) -> SctRepo:
    return SctRepo(db)

def get_model_text_repo(db: OrigTextRepo = Depends(get_db)) -> OrigTextRepo:
    return OrigTextRepo(db)

# ---------------------- Document Adaption ----------------------
def get_document_adaption_service(
    redis_repo: RdsRepo = Depends(get_redis_repo),
    logs_repo: LogRepo = Depends(get_model_logs_repo),
    sct_repo: SctRepo = Depends(get_model_sct_repo),
    recipe_repo: RecipeRepo = Depends(get_model_Recipe_repo),
    text_repo: OrigTextRepo = Depends(get_model_text_repo),
) -> DocSvc:
    return DocSvc(redis_repo, logs_repo, sct_repo, recipe_repo, text_repo)