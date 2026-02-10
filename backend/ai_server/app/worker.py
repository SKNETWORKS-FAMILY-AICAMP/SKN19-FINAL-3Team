import asyncio
import json
from typing import Any, Awaitable, Callable, Optional, List, Dict
from common.schemas import MergeProposalInputData

from common.core.codes import LlmTaskStatus, LlmTaskType
from common.core.config import settings
from common.core.database import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine import LLMEngine
from common.repositories.model_logs_repo import ModelLogsRepository
from common.repositories.redis_repo import RedisRepository
from common.repositories.tag_repo import TagRepository
from common.repositories.doc_recipes_repo import DocRecipesRepository
from common.repositories.original_texts_repo import OriginalTextsRepository
from common.repositories.mixed_repo import MixedRepository  # Import MixedRepository
from common.repositories.secure_token_repo import SecureTokenRepository
from common.repositories.pattern_repo import PatternRepository
from common.util.crypto_masking import InfoMask
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("AI Worker")

# [Worker Startup]
if __name__ == "__main__":
    pass


class WorkerService:
    """
    [Worker Core Service]
    작업(Task) 유형별 비즈니스 로직 및 DB 처리를 캡슐화한 서비스.
    한 번의 세션 연결로 필요한 모든 리포지토리를 초기화하여 사용함.
    """

    def __init__(
        self,
        db: AsyncSession,
        redis_repo: RedisRepository,
        # 필요한 경우 추가 주입
    ):
        self.db = db
        self.redis_repo = redis_repo
        
        # Repositories 초기화
        self.logs_repo = ModelLogsRepository(db)
        self.tag_repo = TagRepository(db)
        
        # 복합 리포지토리 초기화
        self.mixed_repo = MixedRepository(db)
        
        # InfoMask를 위한 Repository 초기화
        self.token_repo = SecureTokenRepository(db)
        self.pattern_repo = PatternRepository(db)
        self.masking_model = InfoMask(self.token_repo, self.pattern_repo)


    async def process_doc_index(self, task_id: str, engine: LLMEngine) -> tuple[dict, Any]:
        """문서 색인(DOC_INDEX) 처리
        1. 로그 조회 (llm_task input, output 기록용)
        2. 기존 문서 데이터 로드
        3. 문서 분할
        4. 카테고리 정보 로드
        5. 문서 색인 및 임베딩 (Engine)
        """
        
        # 1. 로그 조회
        record = await self.logs_repo.get_by_task_id(task_id=task_id)
        if not record or not record.input_data:
            raise ValueError(f"입력 데이터를 찾을 수 없습니다. task_id={task_id}")

        text = record.input_data.get("text")
        recipe_seq = record.input_data.get("recipe_seq")

        if not text:
            raise ValueError(f"입력 텍스트(text)가 누락되었습니다. task_id={task_id}")

        logger.info(f"[문서 조회] 문서 조회 시작 | recipe_seq : {recipe_seq}")

        before_section = None
        
        # 2. 기존 문서 데이터 로드 (수정 모드인 경우)
        if recipe_seq: # 0도 포함 안함
        # if recipe_seq is not None:
            before_section = await self.mixed_repo.get_before_section(recipe_seq)
            
            # 유효성 검사 (필수 키 포함 여부)
            required_keys = {"text_seq", "original_text"}
            if not before_section or not all(required_keys.issubset(item) for item in before_section):
                raise ValueError(f"기존 문서에 대한 유효한 데이터를 찾을 수 없습니다. recipe_seq={recipe_seq}")

            logger.info(f"[문서 조회] 문서 조회 완료")

        # 민감 정보 암호화   
        # logger.info(f"[암호화] 민감정보 암호화 시작")
        # encrypt_start = time.perf_counter()
        # text = await self.masking_model.encrypt_text(text)
        # encrypt_time = time.perf_counter() - encrypt_start
        # logger.info(f"[암호화] 민감정보 암호화 완료 | 소요 시간  : {encrypt_time}")

        # 3. 문서 분할 (Engine)
        logger.info(f"[문서 분할] 문서 분할 시작")
        split_start = time.perf_counter()
        split_texts = await engine.split_document(before_section, text)
        split_time = time.perf_counter() - split_start
        logger.info(f"[문서 분할] 문서 분할 완료 | 현재 섹션 수 : {len(split_texts)} | 소요 시간 : {split_time}")
        
        # 4. 카테고리 정보 로드
        category_list = None
        try:
            category_list_origin = await self.tag_repo.get_category_list()
            # depth별 그룹화 로직 등은 필요시 유지, 여기선 단순화하여 전달하거나 원본 로직 유지
            logger.info(f"[DB 호출] 카테고리 정보 로드 완료")
            
            category_list_depth = {}
            for item in category_list_origin:
                item_summary = {
                    "category": item.tag_name,
                    "summary": item.summary,
                    "vector": item.tag_vector
                }
                category_list_depth[item.depth] = category_list_depth.get(item.depth, [])
                category_list_depth[item.depth].append(item_summary)
            
            category_list = list(category_list_depth.values())
        except Exception as e:
            logger.error(f"[DB 호출] 카테고리 호출 실패 | {e}")

        # 5. 문서 색인 및 임베딩 (Engine)
        logger.info(f"[문서 색인] 문서 색인 시작")
        index_start = time.perf_counter()
        indices = await engine.index_section(split_texts, category_list=category_list)
        index_time = time.perf_counter() - index_start
        logger.info(f"[문서 색인] 문서 색인 완료 | 소요 시간 : {index_time}")
        
        input_data = {"recipe_seq": recipe_seq, "text": text}

        ai_output = indices
        
        return input_data, ai_output



    async def process_doc_update(self, task_id: str, engine: LLMEngine) -> tuple[dict, Any]:
        """문서 업데이트(DOC_UPDATE) 처리"""
        
        # 1. 로그 조회
        record = await self.logs_repo.get_by_task_id(task_id=task_id)
        if not record or not record.input_data:
             raise ValueError(f"입력 데이터를 찾을 수 없습니다. task_id={task_id}")
        
        input_data = record.input_data.get("updates")

        if not input_data :
            raise ValueError(f"입력 데이터의 형식이 알맞지 않습니다. 'input_data' not include key 'updates'")


        logger.info(f"[문서 업데이트] 문서 업데이트 시작 | task_id : {task_id} | 수정 대상 섹션 수 : {len(input_data)}")
        update_start = time.perf_counter()

        # 2. 업데이트 실행 (Engine)
        ai_output = await engine.create_edited_text(input_data)

        update_time = time.perf_counter() - update_start
        logger.info(f"[문서 업데이트] 문서 업데이트 완료 | 소요 시간 : {update_time}")

        return input_data, ai_output


    async def execute_task(self, payload: dict):
        """
        [Template Method] 작업 실행 공통 템플릿
        상태 관리, 예외 처리, 결과 저장을 담당.
        """
        logger.info(f"[Worker 실행] 작업 시작")
        task_start = time.perf_counter()
        task_id = payload.get("task_id")
        if not task_id:
            return
        engine = LLMEngine()

        # 1. 상태: PROCESSING
        await self.redis_repo.set_task_metadata(task_id, LlmTaskStatus.PROCESSING)

        task_type_str = payload.get("task_type")
        try:
            # 2. 작업 라우팅
            task_type = LlmTaskType(task_type_str)
            
            if task_type == LlmTaskType.DOC_INDEX:
                input_data, ai_output = await self.process_doc_index(task_id, engine)
            elif task_type == LlmTaskType.MERGE_PROP:
                input_data, ai_output = await self.process_doc_update(task_id, engine)
            else:
                raise ValueError(f"지원하지 않는 작업 유형입니다: {task_type}")

            # 3. 결과 저장 (ModelLogs)
            await self.logs_repo.update_by_task_id(
                task_id=task_id,
                ai_output=ai_output,
                user_decision=None,
            )

            # 4. 상태: COMPLETE
            await self.redis_repo.set_task_metadata(task_id, LlmTaskStatus.COMPLETED)
            task_time = time.perf_counter() - task_start
            logger.info(f"[Worker 실행] 작업 완료 | 소요 시간 : {task_time}")

        except Exception as e:
            logger.error(f"[Worker 실행] 작업 처리 실패 | task_id : {task_id} | {e}")
            # 상태: ERROR
            await self.redis_repo.set_task_metadata(task_id, LlmTaskStatus.ERROR)
            # 필요 시 에러 로그 DB 저장 로직 추가 가능

async def run_worker():
    """워커 메인 루프"""
    redis_repo = RedisRepository(settings.REDIS_URL)

    logger.info(f"[Worker 실행] Worker 실행 시작 | API: {settings.API_SERVER_URL}")

    while True:
        try:
            # 1. 큐 대기
            payload = await redis_repo.dequeue(timeout=5)
            if not payload:
                continue

            logger.info(f"[Worker 실행] 큐 수신 | payload : {payload}")
            
            task_id = payload.get("task_id")
            if not task_id:
                logger.error(f"[Worker 실행] task_id 누락 | payload : {payload}")
                continue

            # 2. 세션 생성 및 서비스 실행
            # 요청마다 새로운 세션을 열어(Scope) 격리성을 보장
            async with AsyncSessionLocal() as db:
                service = WorkerService(db, redis_repo)
                await service.execute_task(payload)

        except Exception as e:
            logger.info(f"[Worker 실행] Worker loop 실행 중 오류 | {e}")
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(run_worker())
