"""
사용법 참고:

Router는 HTTP 요청을 받아 서비스 계층을 호출하는 용도로만 사용된다.
비즈니스 로직이나 DB 접근은 Service/Repository에 두고 여기서는 라우팅과 응답 스펙만 관리한다.
"""

from uuid import UUID
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from common.schemas import (
    LlmTaskRequest,
    LlmTaskResponse,
    LlmTaskDetailResponse,
    DocProposalResponse,
    DocUpdateRequest,
    DocUpdateResponse,
    DocResponse,
)
from common.core.codes import LlmTaskType, LlmTaskStatus, CodeGroup
from app.services.common_code_service import CommonCodeService as CCSrvc
from app.services.document_adaption import DocumentAdaptionService as DocSvc
from app.api.dependencies import (
    get_common_code_service,
    get_document_adaption_service,
)

router = APIRouter()

@router.get(
    "/tasks/{task_id}/status",
    response_model=LlmTaskResponse,
)
async def get_task_status(
    task_id: str,
    service: DocSvc = Depends(get_document_adaption_service)
):
    """[LLM 작업 상태 조회]

    task_id: UUID
    task_type: 작업 유형
    task_status: 작업 상태
    """
    try:
        status_res = await service.get_task_status(task_id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    return status_res

@router.get(
    "/tasks/{task_id}/detail",
    response_model=LlmTaskDetailResponse,
)
async def get_task_detail(
    task_id: str,
    service: DocSvc = Depends(get_document_adaption_service)
):
    """[LLM 작업 상세 조회]

    task_id: UUID
    task_type: 작업 유형
    task_status: 작업 상태
    results: 작업 결과
    """
    # 1. 상태 조회 (Redis)
    try:
        status_res = await service.get_task_detail(task_id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    return status_res


@router.post("/documents/index", response_model=LlmTaskResponse)
async def request_document_indexing(
    req: LlmTaskRequest,
    service: DocSvc = Depends(get_document_adaption_service),
):
    """[문서 색인 api]
    문서 분할 + 문서 색인
    """
    try:
        return await service.request_document_indexing(req.text)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
@router.get("/documents/proposal", response_model=DocProposalResponse)
async def get_merge_proposal(
    task_id: str,
    service: DocSvc = Depends(get_document_adaption_service),
):
    """[문서 병합 제안 api]"""
    try:
        return await service.get_merge_proposal(task_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/documents/update", response_model=LlmTaskResponse)
async def apply_document_update(
    req: DocUpdateRequest,
    service: DocSvc = Depends(get_document_adaption_service),
):
    """[문서 병합 api]"""

    try:
        return await service.apply_document_update(req)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# [Document/Section] 문서(섹션) 조회 API
@router.get("/documents", response_model=list[DocResponse])
async def get_all_documents(
    skip: int = 0,
    limit: int = 100,
    service: DocSvc = Depends(get_document_adaption_service)
):
    """문서 목록 조회 (중간 발표까지)"""
    return await service.get_all_documents()


@router.get("/documents/{doc_id}", response_model=DocResponse)
async def get_document(
    doc_id: int,
    service: DocSvc = Depends(get_document_adaption_service)
):
    """문서 상세 조회"""
    # 중간 발표용으로 개발되었슴 확인 필요.
    doc = await service.get_document(doc_id)

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document(Recipe) {doc_id} not found",
        )
    return doc