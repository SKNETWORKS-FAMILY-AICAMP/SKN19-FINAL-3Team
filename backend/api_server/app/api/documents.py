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
    DocSearchResponse,
    DocResponse,
    IndexingRequest,
    MergeSelectionResponse,
    DocApplyRequest,
    DocRenameRequest,
)
from common.core.codes import LlmTaskType, LlmTaskStatus, CodeGroup
from app.services.common_code_service import CommonCodeService as CCSrvc
from app.services.document_adaption import DocumentAdaptionService as DocSvc
from app.api.dependencies import get_document_adaption_service
from app.api.admin import admin_router

router = APIRouter()


#--------------------------------------------------------------
# [LLM Task] 작업 상태 관리 API
#--------------------------------------------------------------

@router.get(
    "/tasks/{task_id}/status",
    response_model=LlmTaskResponse,
)
async def get_task_status(
    task_id: str,
    service: DocSvc = Depends(get_document_adaption_service),
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
    service: DocSvc = Depends(get_document_adaption_service),
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


#--------------------------------------------------------------
# [Document CRUD] 문서 조회/검색/수정/삭제 API
#--------------------------------------------------------------

@router.get("/documents", response_model=list[DocResponse])
async def get_all_documents(
    skip: int = 0,
    limit: int = 100,
    service: DocSvc = Depends(get_document_adaption_service),
):
    """문서 목록 조회"""
    return await service.get_all_documents()

@router.get("/documents/search", response_model=list[DocSearchResponse])
async def document_search(
    q: str,
    limit: int = 100,
    type="cloud",
    service: DocSvc = Depends(get_document_adaption_service),
):
    """문서 검색"""
    return await service.document_search(search_word=q, limit=limit, type=type)

@router.get("/documents/proposal", response_model=LlmTaskResponse)
async def get_merge_proposal(
    task_id: str,
    service: DocSvc = Depends(get_document_adaption_service),
):
    """[문서 병합 제안 생성 api]"""
    try:
        return await service.get_merge_proposal(task_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.get("/documents/selection", response_model=MergeSelectionResponse)
async def get_merge_selection(
    task_id: str,
    service: DocSvc = Depends(get_document_adaption_service),
):
    """[문서 병합 선택지 생성 api]"""
    try:
        return await service.get_merge_selection(task_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.get("/documents/{doc_id}", response_model=DocResponse)
async def get_document(
    doc_id: int,
    service: DocSvc = Depends(get_document_adaption_service),
):
    """문서 상세 조회"""
    doc = await service.get_document(doc_id)

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document(Recipe) {doc_id} not found",
        )
    return doc

@router.patch("/documents/{doc_id}/title", status_code=204)
async def rename_document(
    doc_id: int,
    req: DocRenameRequest,
    service: DocSvc = Depends(get_document_adaption_service),
):
    """[문서 이름 변경]"""
    try:
        await service.rename_document(doc_id, req.title)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(
    doc_id: int,
    service: DocSvc = Depends(get_document_adaption_service),
):
    """[문서 삭제]
    
    recipe_seq를 기준으로 문서 및 관련 데이터 삭제
    
    권한 확인:
    - R_ADMIN 또는 R_EDITOR 권한을 가진 사용자만 삭제 가능
    - R_VIEWER 권한은 삭제 불가
    
    삭제 대상:
    - section_recipes: 섹션 레시피 매핑 삭제
    - original_texts: 원본 텍스트 삭제
    - doc_recipes: 문서 레시피 삭제
    - doc_recipe_members: CASCADE로 자동 삭제
    """
    try:
        await service.delete_document(doc_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


#--------------------------------------------------------------
# [Document Processing] 문서 처리/병합 API
#--------------------------------------------------------------

@router.post("/documents/local", status_code=204)
async def request_document_local_save(
    req: IndexingRequest,
    service: DocSvc = Depends(get_document_adaption_service),
):
    """
    문서를 로컬에 저장
    """
    try:
        await service.request_document_local_save(req.recipe_seq, req.text)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/documents/index", response_model=LlmTaskResponse)
async def request_document_indexing(
    req: IndexingRequest,
    service: DocSvc = Depends(get_document_adaption_service),
):
    """[문서 색인 api]
    문서 분할 + 문서 색인
    """
    try:
        return await service.request_document_indexing(req.recipe_seq, req.text)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/documents/apply_final", response_model=LlmTaskResponse)
async def apply_document_update_final(
    request: DocApplyRequest,
    service: DocSvc = Depends(get_document_adaption_service),
):
    """[문서 병합 최종 적용 api]"""
    try:
        return await service.apply_document_update_final(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
