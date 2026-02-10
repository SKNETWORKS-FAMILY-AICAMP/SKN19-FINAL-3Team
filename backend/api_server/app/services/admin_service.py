from sqlalchemy.exc import IntegrityError
from common.repositories.model_logs_repo import ModelLogsRepository
from common.repositories.pattern_repo import PatternRepository
from common.repositories.tag_repo import TagRepository
from common.repositories.user_repo import UserRepository
from common.repositories.doc_permission_repo import DocPermissionRepository

from datetime import datetime
import re

from uuid import UUID
from typing import Optional, List, Any, Dict
from pydantic import TypeAdapter

from common.schemas import (
    Pattern, CreatePatternRequest, ReadPatternResponse, UpdatePatternRequest, DeletePatternRequest,
    DocPermission, CreateDocPermissionRequest, ReadDocPermissionResponse, UpdateDocPermissionRequest, DeleteDocPermissionRequest,
    Category, CreateCategoryRequest, ReadAllCategoriesResponse, UpdateCategoryRequest, DeleteCategoryRequest,
    AuditLog, ReadAuditLogRequest, ReadAuditLogResponse, DeleteAuditLogRequest,
    AccessibleUserInfo, ReadUserResponse
)



class AdminService:
    def __init__(self, audit_log_repo: ModelLogsRepository, 
    pattern_repo: PatternRepository, tag_repo: TagRepository, user_repo: UserRepository,
    doc_permission_repo: DocPermissionRepository):
        self.pattern_repo = pattern_repo
        self.tag_repo = tag_repo
        self.user_repo = user_repo
        self.doc_permission_repo = doc_permission_repo
        self.audit_log_repo = audit_log_repo
        
        # print(type(self.audit_log_repo))

    # region 패턴 관련
    #-------------------------------------------------------------
    # pattern 관련 (API 완료)
    #-------------------------------------------------------------
    async def create_pattern(self, req: CreatePatternRequest) -> Pattern:
        """성공 시 생성된 Pattern, 실패 시 예외 발생"""
        from common.models import Pattern as PatternModel
        try:
            pattern = PatternModel(
                pattern_name=req.pattern_name,
                regex_pattern=req.regex_pattern
            )
            created = await self.pattern_repo.create_pattern(pattern)
            return Pattern(
                pattern_seq=created.pattern_seq,
                pattern_name=created.pattern_name,
                regex_pattern=created.regex_pattern,
                is_active=created.is_active
            )
        except Exception as e:
            print(f"Pattern 생성 실패: {e}")
            raise ValueError(f"Pattern 생성 실패: {e}")


    async def read_all_patterns(self) -> ReadPatternResponse:
        """성공 시 모든 패턴, 실패 시 patterns=[] 반환"""
        try:
            patterns = await self.pattern_repo.read_all_patterns()
            return ReadPatternResponse(
                patterns = [
                    Pattern(
                        pattern_seq=p.pattern_seq,
                        pattern_name=p.pattern_name,
                        regex_pattern=p.regex_pattern,
                        is_active=p.is_active
                    ) for p in patterns
                ]
            )
        except Exception as e:
            print(f"Pattern 조회 실패: {e}")
            return ReadPatternResponse(patterns=[])


    async def update_pattern(self, req: UpdatePatternRequest) -> int:
        """성공 시 1, 실패 시 0 반환"""
        from common.models import Pattern as PatternModel
        try:
            pattern = PatternModel(
                pattern_seq=req.pattern_seq,
                pattern_name=req.pattern_name,
                regex_pattern=req.regex_pattern,
                is_active=req.is_active
            )
            await self.pattern_repo.update_pattern(pattern)
            return 1
        except Exception as e:
            print(f"Pattern 업데이트 실패: {e}")
            return 0


    async def delete_pattern(self, req: DeletePatternRequest) -> int:
        """성공 시 1, 실패 시 0 반환"""
        from common.models import Pattern as PatternModel
        try:
            pattern = PatternModel(pattern_seq=req.pattern_seq)
            await self.pattern_repo.delete_pattern(pattern)
            return 1
        except Exception as e:
            print(f"Pattern 삭제 실패: {e}")
            return 0
    # endregion


    # region 문서 권한 관련
    #-------------------------------------------------------------
    # 문서 권한 관련 (API 완료)
    #-------------------------------------------------------------
    async def create_doc_permission(self, req: CreateDocPermissionRequest) -> int:
        # 성공 시 1, 실패 시 0 반환
        try:
            await self.doc_permission_repo.create_doc_permission(req.recipe_seq, req.user_seq, req.role_code)
            return 1
        except Exception as e:
            print(f"문서 권한 생성 실패: {e}")
            return 0


    async def read_all_doc_permissions(self) -> ReadDocPermissionResponse:
        # 성공 시 모든 문서 권한, 실패 시 [] 반환
        try:
            doc_permissions = await self.doc_permission_repo.read_all_doc_permissions()

            return ReadDocPermissionResponse(
                doc_permissions = [
                    DocPermission(
                        recipe_seq=dp[0].recipe_seq,
                        user_seq=dp[0].user_seq,
                        role_code=dp[0].role_code,
                        doc_name=dp[1],  # doc_name from JOIN
                        user_name=dp[2]  # user_name from JOIN
                    ) for dp in doc_permissions
                ]
            )
        except Exception as e:
            print(f"문서 권한 조회 실패: {e}")
            return ReadDocPermissionResponse(doc_permissions=[])


    async def update_doc_permission(self, req: UpdateDocPermissionRequest) -> int:
        # 성공 시 1, 실패 시 0 반환
        try:
            await self.doc_permission_repo.update_doc_permission(req.recipe_seq, req.user_seq, req.role_code)
            return 1
        except Exception as e:
            print(f"문서 권한 업데이트 실패: {e}")
            return 0


    async def delete_doc_permission(self, req: DeleteDocPermissionRequest) -> int:
        # 성공 시 1, 실패 시 0 반환
        try:
            await self.doc_permission_repo.delete_doc_permission(req.recipe_seq, req.user_seq)
            return 1
        except Exception as e:
            print(f"문서 권한 삭제 실패: {e}")
            return 0
    # endregion


    # region 카테고리 관련
    #-------------------------------------------------------------
    # 카테고리(태그) 관련 (API 완료)
    #-------------------------------------------------------------
    async def create_category(self, req: CreateCategoryRequest) -> int:
        try:
            await self.tag_repo.create_category(req.tag_name, req.depth, req.summary)
            return 1
        except Exception as e:
            print(f"Tag 생성 실패: {e}")
            return 0


    async def read_all_categories(self) -> ReadAllCategoriesResponse:
        # 성공 시 모든 카테고리, 실패 시 [] 반환
        try:
            categories = await self.tag_repo.read_all_categories()
            return ReadAllCategoriesResponse(
                categories = [
                    Category(
                        tag_seq=cat.tag_seq,
                        tag_name=cat.tag_name,
                        depth=cat.depth,
                        summary=cat.summary,
                        created_at=cat.created_at
                    ) for cat in categories
                ]
            )
        except Exception as e:
            print(f"Tag 조회 실패: {e}")
            return ReadAllCategoriesResponse(categories=[])


    async def update_category(self, req: UpdateCategoryRequest) -> int:
        # 성공 시 1, 실패 시 0 반환
        try:
            await self.tag_repo.update_category(req.tag_seq, req.tag_name, req.depth, req.summary)
            return 1
        except Exception as e:
            print(f"Tag 업데이트 실패: {e}")
            return 0


    async def delete_category(self, req: DeleteCategoryRequest) -> int:
        # 성공 시 1, 실패 시 0 반환
        try:
            await self.tag_repo.delete_category(req.tag_seq)
            return 1
        except Exception as e:
            print(f"Tag 삭제 실패: {e}")
            return 0
    # endregion


    # region 감사 로그 관련
    #-------------------------------------------------------------
    # 감사 로그 관련 (API 완료)
    #-------------------------------------------------------------
    async def read_audit_log(self, req: ReadAuditLogRequest) -> ReadAuditLogResponse:
        # 성공 시 검색 필터링 된 감사 로그, 실패 시 빈 리스트 반환
        try:
            logs = await self.audit_log_repo.read_audit_log(
                start_date=req.start_date, 
                end_date=req.end_date, 
                task_type_code=req.task_type_code, 
                operator_seq=req.operator_seq, 
                team_seq=req.team_seq
            )
            
            return ReadAuditLogResponse(
                audit_logs = [
                    AuditLog(
                        log_seq=log.log_seq,
                        task_type_code=log.task_type_code,
                        operator_seq=log.operator_seq,
                        team_seq=log.team_seq,
                        task_id=log.task_id,
                        start_task_id=log.start_task_id,
                        created_at=log.created_at
                    )
                    for log in logs
                ]
            )
        except Exception as e:
            print(f"감사 로그 조회 실패: {e}")
            return ReadAuditLogResponse(audit_logs=[])
    # endregion


    # region 사용자 관련
    #-------------------------------------------------------------
    # 사용자 관련 (API 완료)
    #-------------------------------------------------------------
    async def read_all_users(self) -> ReadUserResponse:
        users = await self.user_repo.read_all_users()
    
        return ReadUserResponse(
            users = [
                AccessibleUserInfo(
                    user_seq=u.user_seq,
                    display_name=u.display_name,
                    username=u.username,
                    status_code=u.status_code,
                    created_at=u.created_at,
                )
                for u in users
            ]
        )
    # endregion