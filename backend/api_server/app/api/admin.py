"""
관리자 전용 API 라우터

Router는 HTTP 요청을 받아 서비스 계층을 호출하는 용도로만 사용된다.
비즈니스 로직이나 DB 접근은 Service/Repository에 두고 여기서는 라우팅과 응답 스펙만 관리한다.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from common.schemas import (
    CreatePatternRequest,
    ReadPatternResponse,
    UpdatePatternRequest,
    DeletePatternRequest,

    CreateDocPermissionRequest,
    ReadDocPermissionResponse,
    UpdateDocPermissionRequest,
    DeleteDocPermissionRequest,
    
    CreateCategoryRequest,
    UpdateCategoryRequest,
    DeleteCategoryRequest,
    ReadAllCategoriesResponse,
    ReadAuditLogResponse,
    ReadAuditLogRequest,
    ReadUserResponse,
)
from app.services.admin_service import AdminService as AdminSvc
from app.api.dependencies import get_admin_service

admin_router = APIRouter()


#--------------------------------------------------------------
# [관리자/암호화 관리] CRUD API
#--------------------------------------------------------------

@admin_router.post("/admin/create_pattern")
async def create_pattern(
    req: CreatePatternRequest,
    service: AdminSvc = Depends(get_admin_service),
):
    """
    [관리자] 암호 생성
    """
    try:
        result = await service.create_pattern(req)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return result

@admin_router.post("/admin/read_all_patterns", response_model=ReadPatternResponse)
async def read_all_patterns(
    service: AdminSvc = Depends(get_admin_service),
):
    """
    [관리자] 암호 조회
    """
    try:
        result = await service.read_all_patterns()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return result

@admin_router.post("/admin/update_pattern")
async def update_pattern(
    req: UpdatePatternRequest,
    service: AdminSvc = Depends(get_admin_service),
):
    """
    [관리자] 암호 수정
    """
    try:
        result = await service.update_pattern(req)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return result

@admin_router.post("/admin/delete_pattern")
async def delte_pattern(
    req: DeletePatternRequest,
    service: AdminSvc = Depends(get_admin_service),
):
    """
    [관리자] 암호 삭제
    """
    try:
        result = await service.delete_pattern(req)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return result



#--------------------------------------------------------------
# [관리자/문서 권한 관리] CRUD API
#--------------------------------------------------------------

@admin_router.post("/admin/create_doc_permission")
async def create_doc_permission(
    req: CreateDocPermissionRequest,
    service: AdminSvc = Depends(get_admin_service),
):
    """
    [관리자] 문서 권한 생성
    """
    try:
        result = await service.create_doc_permission(req)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return result

@admin_router.post("/admin/read_all_doc_permissions", response_model=ReadDocPermissionResponse)
async def read_all_doc_permissions(
    service: AdminSvc = Depends(get_admin_service),
):
    """
    [관리자] 문서 권한 조회
    """
    try:
        result =  await service.read_all_doc_permissions()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return result

@admin_router.post("/admin/update_doc_permission")
async def update_doc_permission(
    req: UpdateDocPermissionRequest,
    service: AdminSvc = Depends(get_admin_service),
):
    """
    [관리자] 문서 권한 수정
    """
    try:
        result = await service.update_doc_permission(req)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return result

@admin_router.post("/admin/delete_doc_permission")
async def delete_doc_permission(
    req: DeleteDocPermissionRequest,
    service: AdminSvc = Depends(get_admin_service),
):
    """
    [관리자] 문서 권한 삭제
    """
    try:
        result = await service.delete_doc_permission(req)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return result

#--------------------------------------------------------------
# [관리자/카테고리 관리] CRUD API
#--------------------------------------------------------------

@admin_router.post("/admin/create_category")
async def create_category(
    req: CreateCategoryRequest,
    service: AdminSvc = Depends(get_admin_service),
):
    """
    [관리자] 카테고리 생성
    """
    try:
        result = await service.create_category(req)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return result

@admin_router.post("/admin/read_all_categories", response_model=ReadAllCategoriesResponse)
async def read_category(
    service: AdminSvc = Depends(get_admin_service),
):
    """
    [관리자] 카테고리 조회
    """
    try:
        result = await service.read_all_categories()        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return result

@admin_router.post("/admin/update_category")
async def update_category(
    req: UpdateCategoryRequest,
    service: AdminSvc = Depends(get_admin_service),
):
    """
    [관리자] 카테고리 수정
    """
    try:
        result = await service.update_category(req)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return result

@admin_router.post("/admin/delete_category")
async def delete_category(
    req: DeleteCategoryRequest,
    service: AdminSvc = Depends(get_admin_service),
):
    """
    [관리자] 카테고리 삭제
    """
    try:
        result = await service.delete_category(req)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return result


#--------------------------------------------------------------
# [관리자/감사 로그] CRUD API (read만 필요)
#--------------------------------------------------------------

@admin_router.post("/admin/read_audit_log", response_model=ReadAuditLogResponse)
async def read_audit_log(
    req: ReadAuditLogRequest,
    service: AdminSvc = Depends(get_admin_service),
):
    """
    [관리자] 감사 로그 조회
    """
    try:
        result = await service.read_audit_log(req)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return result


#--------------------------------------------------------------
# [관리자/사용자] CRUD API (read만 필요)
#--------------------------------------------------------------

@admin_router.post("/admin/read_all_users", response_model=ReadUserResponse)
async def read_all_users(
    service: AdminSvc = Depends(get_admin_service),
):
    """
    [관리자] 사용자 조회
    """
    try:
        result = await service.read_all_users()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return result
