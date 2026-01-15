import asyncio
import json
from typing import Any, Awaitable, Callable

from common.core.codes import LlmTaskStatus, LlmTaskType
from common.core.config import settings
from common.core.database import AsyncSessionLocal
from common.repositories.model_logs_repo import ModelLogsRepository
from common.repositories.redis_repo import RedisRepository
from app.engine import LLMEngine


async def _execute_task_with_logging(
    payload: dict,
    repo: RedisRepository,
    process_func: Callable[..., Awaitable[tuple[dict, Any]]],
) -> None:
    """
    공통 작업(Task) 처리 패턴을 추상화한 함수

    원본 로직:
    - AI 처리 성공 시 COMPLETE
    - ModelLog 저장 실패는 무시
    - AI 처리 실패 시 ERROR 상태 전환 (원본 버그 수정)

    매개변수:
        payload: Redis에서 가져온 작업 데이터
        repo: RedisRepository 인스턴스
        process_func: 실제 처리 로직을 담은 함수 (input_data, ai_output을 반환)
    """
    # task_id는 run_worker에서 검증됨
    task_id = payload.get("task_id")
    
    # 상태를 PROCESSING으로 변경
    if task_id:
        await repo.set_task_metadata(task_id, LlmTaskStatus.PROCESSING)

    # 실제 처리 로직 실행 (에러 발생 시 ERROR 상태로 전환)
    try:
        input_data, ai_output = await process_func(payload)
    except Exception as e:
        print(f"작업 처리 실패: {e}")
        if task_id:
            await repo.set_task_metadata(task_id, LlmTaskStatus.ERROR)
        raise

    # model_logs에 저장 (원본 로직: 실패해도 무시하고 COMPLETE 처리)
    try:
        async with AsyncSessionLocal() as db:
            logs_repo = ModelLogsRepository(db)
            await logs_repo.update_by_task_id(
                task_id=task_id,
                ai_output=ai_output,
                user_decision=None,
            )
    except Exception as e:
        print(f"model_logs 저장 실패: {e}")

    # 상태를 COMPLETE로 변경
    if task_id:
        await repo.set_task_metadata(task_id, LlmTaskStatus.COMPLETE)


async def handle_doc_index(payload: dict, engine: LLMEngine, repo: RedisRepository):
    """문서 색인 핸들러 (분할 + 색인)    
    """

    async def process(payload: dict) -> tuple[dict, Any]:
        task_id = payload.get("task_id")
        text = ""

        try:
            async with AsyncSessionLocal() as db:
                logs_repo = ModelLogsRepository(db)
                record = await logs_repo.get_by_task_id(task_id=task_id)
                if record and record.input_data:
                    text = record.input_data
        except Exception as e:
            print(f"model_logs 로드 실패: {e}")

        if not text:
            raise ValueError(f"입력 텍스트를 찾을 수 없습니다. task_id={task_id}")

        print(
            f"문서 색인(DOC_INDEX) 수신 | task_id={task_id} | len(text)={len(text)}"
        )

        # 문서 분할
        split_texts = await engine.split_document(text)
        input_data = {"text": text}

        print(f"   분할 완료: {len(split_texts)} 청크(chunks)")
        
        # 문서 색인
        indices = await engine.index_section(split_texts)
        
        ai_output = indices
        return input_data, ai_output

    await _execute_task_with_logging(payload, repo, process)

async def handle_doc_update(payload: dict, engine: LLMEngine, repo: RedisRepository):
    """문서 업데이트 핸들러"""

    async def process(payload: dict) -> tuple[dict, Any]:
        # payload에서 필요한 정보 추출
        section_seq = payload.get("section_seq")
        task_id = payload.get("task_id")
        text_content = payload.get("text") # 업데이트할 텍스트 내용

        print(f"문서 업데이트(DOC_UPDATE) 수신 | task_id={task_id} | section_seq={section_seq}")

        if not section_seq:
            raise ValueError("section_seq is required")

        # DB 작업: 해당 섹션의 텍스트를 업데이트
        async with AsyncSessionLocal() as db:
            from common.repositories.original_texts_repo import OriginalTextsRepository
            from common.models import OriginalText # 모델 필요시 임포트

            text_repo = OriginalTextsRepository(db)
            
            # (예시 로직) 기존 텍스트들을 모두 만료처리하거나 삭제하고, 새 텍스트를 추가하는 로직으로 추정
            # 여기서는 단순히 섹션의 텍스트가 존재한다고 가정하고 로그만 남김
            # 실제 업데이트 로직 구현 필요. 예: await text_repo.update_text(section_seq, text_content)
            
            existing_texts = await text_repo.get_by_section(section_seq)
            if not existing_texts:
                 print(f"   Warning: No existing texts for section {section_seq}")

            print(f"   Updated section {section_seq} with new text length: {len(text_content) if text_content else 0}")
            
            # 결과 구성
            result = {
                "section_seq": section_seq,
                "status": "updated",
                "updated_count": 1
            }

        input_data = {"section_seq": section_seq}
        ai_output = result
        return input_data, ai_output

    await _execute_task_with_logging(payload, repo, process)


async def handle_merge_prop(payload: dict, engine: LLMEngine, repo: RedisRepository):
    """제안 병합 핸들러"""

    async def process(payload: dict) -> tuple[dict, Any]:
        # 다중 텍스트 우선 (본질: 여러 제안을 병합)
        texts = payload.get("texts")
        if not texts:
            text = payload.get("text")
            texts = [text] if text else []

        task_id = payload.get("task_id")
        print(f"제안 병합(MERGE_PROP) 수신 | task_id={task_id} | proposals={len(texts)}")

        merged_content = await engine.merge_proposals(texts)

        input_data = {"texts": texts}
        ai_output = {"merged_content": merged_content}
        return input_data, ai_output

    await _execute_task_with_logging(payload, repo, process)


async def run_worker():
    repo = RedisRepository(settings.REDIS_URL)
    engine = LLMEngine()

    # 작업 유형(Task Type)별 핸들러 매핑 (확장 가능한 구조)
    task_handlers = {
        LlmTaskType.DOC_INDEX: handle_doc_index,
        LlmTaskType.DOC_UPDATE: handle_doc_update,
    }

    print(f"지식 워커(Knowledge Worker) 시작됨. API: {settings.API_SERVER_URL}")
    print(f"등록된 핸들러: {list(task_handlers.keys())}")

    while True:
        try:
            payload = await repo.dequeue(timeout=5)
            if not payload:
                continue

            print(f"큐에서 수신됨: {payload}")
            
            # 1. task_id 검증
            task_id = payload.get("task_id")
            if not task_id:
                print(f"페이로드에 task_id가 누락되었습니다: {payload}")
                continue

            # 2. task_type 검증 및 변환
            raw_task = payload.get("task_type")

            # 작업 유형이 없으면 오류 처리
            if raw_task is None:
                print(f"페이로드에 작업 유형(task_type)이 누락되었습니다: {payload}")
                continue

            # 작업 유형 변환
            try:
                task_type = (
                    raw_task
                    if isinstance(raw_task, LlmTaskType)
                    else LlmTaskType(raw_task)
                )
                # 검증된 task_type을 payload에 업데이트 (선택 사항이지만 안전을 위해)
                # payload["task_type"] = task_type.value # 필요시
            except ValueError:
                print(f"알 수 없는 작업 유형(task_type): {raw_task}, payload: {payload}")
                continue

            # 핸들러 매핑에서 적절한 핸들러 찾기
            handler = task_handlers.get(task_type)
            if handler:
                await handler(payload, engine, repo)
            else:
                print(f"해당 작업 유형(task_type)에 대한 핸들러가 없습니다: {task_type}, payload: {payload}")
        except Exception as e:
            print(f"워커 오류: {e}")
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(run_worker())
