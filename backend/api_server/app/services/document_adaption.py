
from common.repositories.redis_repo import RedisRepository
from common.repositories.model_logs_repo import ModelLogsRepository
from common.repositories.section_repo import SectionRepository
from common.repositories.doc_recipes_repo import DocRecipesRepository
from common.repositories.original_texts_repo import OriginalTextsRepository
from uuid import UUID
from typing import Optional, List

from common.schemas import (
    LlmTaskRequest,
    LlmTaskResponse,
    LlmTaskDetailResponse,
    DocResponse,
    DocProposalResponse,
    DocUpdateRequest
)
from common.core.codes import LlmTaskType, LlmTaskStatus
import uuid, json


class DocumentAdaptionService:
    """
    [AJC Core Service]
    외부 문서를 시스템의 지식 체계(Context)에 맞게 '적응(Adapt)'시키는 워크플로우
    """

    def __init__(
        self,
        redis_repo: RedisRepository,
        logs_repo: Optional[ModelLogsRepository] = None,
        sct_repo: Optional[SectionRepository] = None,
        recipe_repo: Optional[DocRecipesRepository] = None,
        text_repo: Optional[OriginalTextsRepository] = None,
    ):
        self.redis_repo = redis_repo
        self.logs_repo = logs_repo
        self.sct_repo = sct_repo
        self.recipe_repo = recipe_repo
        self.text_repo = text_repo

    async def request_document_indexing(self, text) -> LlmTaskResponse:
        """[문서 색인] 분할 + 색인"""
        if not self.logs_repo:
            raise ValueError("ModelLogsRepository not injected")

        task_id = uuid.uuid4()
        task_type = LlmTaskType.DOC_INDEX
        task_status = LlmTaskStatus.PENDING

        payload = {
            "task_id": str(task_id),
            "task_type": task_type.value,
            "task_status": task_status.value,
            # "text": text,
        }

        await self.logs_repo.create(
            operator_seq=None,
            team_seq=None,
            task_type_code=task_type,
            task_id=task_id,
            input_data=text,
            ai_output=None,
            user_decision=None,
        )
        await self.redis_repo.enqueue(key_name="task_id", payload=payload)

        return LlmTaskResponse(
            task_id=task_id,
            task_type=task_type,
            task_status=task_status
        )
    
    async def _fetch_task_state_from_redis(self, task_id: str):
        """Redis에서 작업 메타데이터 조회 및 파싱 (공통 로직)"""
        meta = await self.redis_repo.get_task_metadata(task_id)

        if not meta:
            raise KeyError("작업을 찾을 수 없습니다.")
        
        task_status = None
        task_type = None

        if "task_status" in meta:
            try:
                task_status = LlmTaskStatus(meta["task_status"])
            except ValueError:
                raise KeyError("작업 상태를 찾을 수 없습니다.")
        
        if "task_type" in meta:
            try:
                task_type = LlmTaskType(meta["task_type"])
            except ValueError:
                raise ValueError("알 수 없는 작업 상태입니다.")
        
        return task_status, task_type

    async def get_task_status(self, task_id: str) -> LlmTaskDetailResponse:
        task_status, task_type = await self._fetch_task_state_from_redis(task_id)

        return LlmTaskDetailResponse(
            task_id=uuid.UUID(task_id),
            task_type=task_type,
            task_status=task_status,
            results=None
        )

    async def get_task_detail(self, task_id: str) -> LlmTaskDetailResponse:
        # 1. Redis 조회 (공통 로직 사용)
        task_status, task_type = await self._fetch_task_state_from_redis(task_id)

        # 2. DB 조회 (로그가 있으면 완료된 작업)
        log = None
        if self.logs_repo:
            try:
                uuid_obj = uuid.UUID(task_id)
                log = await self.logs_repo.get_by_task_id(uuid_obj)
            except (ValueError, TypeError):
                # 로그 조회 실패 시 Redis 상태만 반환하기 위해 무시하거나 에러 처리
                # 기존 로직: raise KeyError("작업 상태를 찾을 수 없습니다.")
                raise KeyError("작업 상태를 찾을 수 없습니다.")

        if log:
            return LlmTaskDetailResponse(
                task_id=log.task_id,
                task_type=LlmTaskType(log.task_type_code),
                task_status=LlmTaskStatus.COMPLETE,
                results={
                    "input_data": log.input_data,
                    "ai_output": log.ai_output
                }
            )

        if task_status and task_type:
            return LlmTaskDetailResponse(
                task_id=uuid.UUID(task_id),
                task_type=task_type,
                task_status=task_status,
                results=None
            )

        raise ValueError("Task not found")

    async def get_all_documents(self) -> Optional[List[DocResponse]]:
        """문서 목록 조회 (중간 발표까지)"""
        return await self.recipe_repo.get_all()
    
    async def get_document(self, recipe_seq: int) -> Optional[DocResponse]:
        """# 중간 발표용으로 개발되었슴 확인 필요."""
        recipe = await self.recipe_repo.get_by_seq(recipe_seq)
        if not recipe:
            return None

        # 기본 값 설정
        final_recipe_value = recipe.recipe_value
        final_title = None
        final_text = None

        if recipe.recipe_value and isinstance(recipe.recipe_value, str):
            try:
                # 1. JSON parsing
                parsed_value = json.loads(recipe.recipe_value)
                final_recipe_value = parsed_value

                # 2. Extract text_seqs and fetch OriginalTexts
                if isinstance(parsed_value, list):
                    texts = []
                    for item in parsed_value:
                        if isinstance(item, int):
                            text_obj = await self.text_repo.get_by_text_seq(item)
                            if text_obj:
                                texts.append(text_obj.original_text)
                    
                    # 3. Populate 'text' field
                    if texts:
                        final_text = "\n\n".join(texts)
                        first_line = texts[0].split('\n')[0]
                        final_title = first_line.replace('#', '').strip()

            except ValueError:
                pass
        
        # 새로운 객체(DTO) 생성 반환
        return DocResponse(
            recipe_seq=recipe.recipe_seq,
            doc_type_code=recipe.doc_type_code,
            recipe_value=final_recipe_value,
            created_at=recipe.created_at,
            updated_at=recipe.updated_at,
            title=final_title,
            text=final_text
        )
    
    async def get_merge_proposal(self, task_id: str) -> Optional[DocProposalResponse]:

        # task_id 로 섹션+색인 정보 조회
        # 후처리
        # 
        return DocProposalResponse(
        **DocProposalResponse.Config.json_schema_extra.get("example")
    )

    async def apply_document_update(self, req: DocUpdateRequest) -> Optional[LlmTaskResponse]:
        
        return LlmTaskResponse(
            task_id=uuid.uuid4(),
            task_type=LlmTaskType.DOC_UPDATE,
            task_status=LlmTaskStatus.PENDING
        )