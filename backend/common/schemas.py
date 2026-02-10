"""
사용법 참고:

schemas.py는 요청/응답 DTO를 정의한다. 검증/직렬화 스펙만 담고,
비즈니스 로직이나 DB 접근은 포함하지 않는다.
"""

from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

from common.core.codes import (
    LlmTaskStatus,
    LlmTaskType,
    MergeProposalType,
    MergeActionType,
)
from pydantic import BaseModel, Field

# region [Indexing]


class IndexingRequest(BaseModel):
    """LLM 인덱싱 요청 DTO
    DTO = Data Transfer Object
    분할 + 인덱싱
    """

    recipe_seq: int = 0
    text: Optional[str]


class IndexingAiOutput(BaseModel):
    tag: Optional[str] = None
    essence: Optional[str] = None
    text_seq: Optional[int] = None
    section_seq: Optional[int] = None
    original_text: Optional[str] = None
    essence_vector: Optional[List[float]] = None
    merge_action_type: MergeActionType
    related_recipe_seq: Optional[List[int]] = None
    score: Optional[float] = None


# endregion


class MergePropRequest(BaseModel):
    task_id: UUID
    start_task_id: UUID
    sections: List[IndexingAiOutput]


class LlmTaskRequest(BaseModel):
    """LLM 작업 공통 요청 DTO
    DTO = Data Transfer Object
    """

    text: Optional[str] = None  # 단건일때
    texts: Optional[List[str]] = None  # 다건일때
    k: Optional[int] = None  # 검색 시 상위 k개 조회


class LlmTaskResponse(BaseModel):
    """LLM 작업 공통 응답 DTO"""

    task_id: UUID
    task_type: LlmTaskType
    task_status: LlmTaskStatus
    recipe_seq: Optional[int] = None  # 문서 생성/업데이트 시 반환되는 recipe_seq


class LlmTaskDetailResponse(BaseModel):
    """작업 상태 및 결과 통합 응답 DTO"""

    task_id: UUID
    task_type: LlmTaskType
    task_status: LlmTaskStatus
    results: Optional[Union[dict, list]] = None


# [Common Code] 생성 요청
class CommonCodeCreate(BaseModel):
    code_group: str
    code_value: str
    code_name: str
    is_use: bool = True


# [Common Code] 응답
class CommonCodeResponse(BaseModel):
    code_seq: int
    code_group: str
    code_value: str
    code_name: str
    is_use: bool

    class Config:
        from_attributes = True


# ----------------------------------------------


class DocProposalSection(BaseModel):
    is_changed: bool
    text_seq: int
    section_seq: int
    original_text: str


class DocUpdateSection(BaseModel):
    is_merge: bool = True
    recipe_seq: int
    title: Optional[str] = None
    sections: List[DocProposalSection]


class DocProposalResponse(BaseModel):
    task_id: UUID
    merge_proposal_type: MergeProposalType = MergeProposalType.PROPOSAL_REQUIRED
    target_recipes: Optional[List[DocUpdateSection]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "123e4567-e89b-12d3-a456-uuid00000000",
                "merge_proposal_type": "PROPOSAL_REQUIRED",
                "target_recipes": [
                    # 변경 제안된 문서 1개
                    {
                        "is_merge": True,  # 병합 여부
                        "recipe_seq": 1,
                        "title": "내부 기획서",
                        "sections": [
                            {
                                # True면 적용 대상, front에서 하이라이트 처리
                                "is_changed": True,
                                "text_seq": 1,
                                "section_seq": 2,
                                # True면 새로 분할된 섹션의 텍스트
                                "original_text": "새로 분할된 섹션의 텍스트",
                            },
                            {
                                # False면 적용 대상이 아님, 일반 문서 처럼 보임
                                "is_changed": False,
                                "text_seq": 2,
                                "section_seq": 3,
                                # False면 (구) 문서의 텍스트
                                "original_text": "원문 텍스트 (ex: 동해물과 백두산이)",
                            },
                        ],
                    },
                    {
                        "is_merge": True,  # 병합 여부
                        "recipe_seq": 2,
                        "title": "외부 기획서",
                        "sections": [
                            {
                                # True면 적용 대상, front에서 하이라이트 처리
                                "is_changed": True,
                                "text_seq": 1,
                                "section_seq": 2,
                                # True면 새로 분할된 섹션의 텍스트
                                "original_text": "새로 분할된 섹션의 텍스트",
                            },
                            {
                                # False면 적용 대상이 아님, 일반 문서 처럼 보임
                                "is_changed": False,
                                "text_seq": 2,
                                "section_seq": 3,
                                # False면 (구) 문서의 텍스트
                                "original_text": "원문 텍스트 (ex: 동해물과 백두산이)",
                            },
                        ],
                    },
                ],
            }
        }


# [Document Update] 병합 업데이트 요청
class DocUpdateRequest(BaseModel):
    task_id: UUID
    target_recipes: List[DocUpdateSection]

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "123e4567-e89b-12d3-a456-uuid00000000",
                "target_recipes": [
                    {
                        "is_merge": True,  # 병합 여부
                        "recipe_seq": 1,
                        "sections": [
                            {
                                # True면 적용 대상, front에서 하이라이트 처리
                                "is_changed": True,
                                "text_seq": 1,
                                "section_seq": 2,
                                # True면 새로 분할된 섹션의 텍스트
                                "original_text": "새로 분할된 섹션의 텍스트",
                            },
                            {
                                # False면 적용 대상이 아님, 일반 문서 처럼 보임
                                "is_changed": False,
                                "text_seq": 2,
                                "section_seq": 3,
                                # False면 (구) 문서의 텍스트
                                "original_text": "원문 텍스트 (ex: 동해물과 백두산이)",
                            },
                        ],
                    },
                    {
                        "is_merge": False,  # 병합 여부
                        "recipe_seq": 2,
                        "sections": [
                            {
                                # True면 적용 대상, front에서 하이라이트 처리
                                "is_changed": True,
                                "text_seq": 1,
                                "section_seq": 2,
                                # True면 새로 분할된 섹션의 텍스트
                                "original_text": "새로 분할된 섹션의 텍스트",
                            },
                            {
                                # False면 적용 대상이 아님, 일반 문서 처럼 보임
                                "is_changed": False,
                                "text_seq": 2,
                                "section_seq": 3,
                                # False면 (구) 문서의 텍스트
                                "original_text": "원문 텍스트 (ex: 동해물과 백두산이)",
                            },
                        ],
                    },
                ],
            }
        }


class DocUpdateResponse(BaseModel):
    task_id: UUID
    task_type: LlmTaskType
    task_status: LlmTaskStatus
    section_seq: int

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "123e4567-e89b-12d3-a456-uuid00000000",
                "task_type": "DOC_UPDATE",
                "task_status": "PENDING",
            }
        }


class DocResponse(BaseModel):
    recipe_seq: int
    doc_type_code: str
    title: Optional[str] = None
    text: Optional[str] = None
    recipe_value: Optional[Union[dict, list, str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocSearchResponse(BaseModel):
    id: int
    title: str
    type: str
    preview: str


# ----------------------------------------------
# [Auth] Schema
class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    display_name: str
    username: str
    password: str


class UserResponse(BaseModel):
    user_seq: int
    display_name: str
    username: str
    status_code: str
    created_at: datetime

    class Config:
        from_attributes = True


# [Privacy] Schema
class PrivacyPatternCreate(BaseModel):
    pattern_name: str
    regex_pattern: str

class PrivacyPatternResponse(BaseModel):
    pattern_seq: int
    pattern_name: str
    regex_pattern: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True



# region 관리자

# 패턴 관리 관련
class Pattern(BaseModel):
    pattern_seq: int
    pattern_name: str
    regex_pattern: str
    is_active: bool

class CreatePatternRequest(BaseModel):
    pattern_name: str
    regex_pattern: str
class ReadPatternResponse(BaseModel):
    patterns: List[Pattern]
class UpdatePatternRequest(BaseModel):
    pattern_seq: int
    pattern_name: str
    regex_pattern: str
    is_active: bool
class DeletePatternRequest(BaseModel):
    pattern_seq: int

# 문서 권한 관련
class DocPermission(BaseModel):
    recipe_seq: int
    user_seq: int
    role_code: str
    doc_name: Optional[str] = None
    user_name: Optional[str] = None

class CreateDocPermissionRequest(BaseModel):
    recipe_seq: int
    user_seq: int
    role_code: str
class ReadDocPermissionResponse(BaseModel):
    doc_permissions: List[DocPermission]
class UpdateDocPermissionRequest(BaseModel):
    recipe_seq: int
    user_seq: int
    role_code: str
class DeleteDocPermissionRequest(BaseModel):
    recipe_seq: int
    user_seq: int

# 카테고리 관련
# 카테고리와 Tag는 동일. 다만, Tag Schema는 미존재
# 관리자 페이지에서 사용하기 위해 별도의 Schema로 정의
class Category(BaseModel):
    tag_seq: int
    tag_name: str
    depth: int
    summary: str
    # tag_vector: List[float]
    created_at: datetime

class CreateCategoryRequest(BaseModel):
    tag_name: str
    depth: int
    summary: str
    
class ReadAllCategoriesResponse(BaseModel):
    categories: List[Category]

class UpdateCategoryRequest(BaseModel):
    tag_seq: int
    tag_name: str
    depth: int
    summary: str
class DeleteCategoryRequest(BaseModel):
    tag_seq: int

# 감사 로그 관련
class AuditLog(BaseModel):
    log_seq: int
    operator_seq: Optional[int] = None
    team_seq: Optional[int] = None
    task_type_code: str
    task_id: UUID
    start_task_id: UUID
    created_at: datetime

class ReadAuditLogRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    task_type_code: Optional[str] = None
    operator_seq: Optional[int] = None
    team_seq: Optional[int] = None

class ReadAuditLogResponse(BaseModel):
    audit_logs: List[AuditLog]

class DeleteAuditLogRequest(BaseModel):
    log_seq: int

# 사용자 관련
class AccessibleUserInfo(BaseModel):
    user_seq: int
    display_name: str
    username: str
    status_code: str
    created_at: datetime

class ReadUserResponse(BaseModel):
    users: List[AccessibleUserInfo]

# endregion 관리자



class TokenizeRequest(BaseModel):
    text: str


class TokenizeResponse(BaseModel):
    tokenized_text: str


class MergeSectionItem(BaseModel):
    merge_action_type: Optional[MergeActionType] = None
    text_seq: Optional[int] = None
    section_seq: Optional[int] = None
    essence: Optional[str] = None
    essence_vector: Optional[List[float]] = None
    original_text: Optional[str] = None
    related_recipe_seq: Optional[List[int]] = None
    tag: Optional[str] = None
    score: Optional[float] = None
    before_text: Optional[str] = None
    after_text: Optional[str] = None
    related_recipe_seq: Optional[List[int]] = Field(None, alias="target_recipes")
    related_texts: Optional[List[dict]] = None


class MergeProposalInputData(BaseModel):
    recipe_seq: int
    section_list: List[MergeSectionItem] = Field(alias="updates")


class MergeProposalTargetRecipe(BaseModel):
    recipe_seq: int
    text_seq_list: List[int]


class MergeProposalInputDataV2(BaseModel):
    recipe_seq: int
    section_list: List[MergeSectionItem] = Field(alias="updates")
    merge_proposal_target_recipe_list: Optional[List[MergeProposalTargetRecipe]] = None


class MergeText(BaseModel):
    is_changed: bool
    text_seq: int
    section_seq: int
    text_before: str
    text_after: Optional[str] = None


class MergeRecipe(BaseModel):
    recipe_seq: int
    is_merge: bool = True
    title: Optional[str] = None
    doc_type_code: Optional[str] = None
    texts: List[MergeText]


class GeneratedTextItem(BaseModel):
    text_seq: int 
    section_seq: int
    original_text: str



class MergeSelectionResponse(BaseModel):
    task_id: UUID
    recipes: List[MergeRecipe]

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "123e4567-e89b-12d3-a456-uuid00000000",
                "recipes": [
                    {
                        "recipe_seq": 1,
                        "is_merge": True, # 기본값: True
                        "texts": [
                            {
                                "is_changed": True,
                                "text_seq": 1,
                                "section_seq": 1,
                                "text_before": "(변경O) 동해물과 백두산이 마르고 닳도록",
                                "text_after": "(변경O) 서해물과 백두산이 마르고 닳도록",
                            },
                            {
                                "is_changed": False,
                                "text_seq": 2,
                                "section_seq": 2,
                                "text_before": "(변경X) 하느님이 보우하사 우리나라 만세",
                                "text_after": "(변경X) 하느님이 보우하사 우리나라 만세",
                            }
                        ],
                    },
                    {
                        "recipe_seq": 3,
                        "is_merge": True, # 기본값: True
                        "sections": [
                            {
                                "is_changed": True,
                                "text_seq": 1,
                                "section_seq": 1,
                                "text_before": "(변경O) 동해물과 백두산이 마르고 닳도록",
                                "text_after": "(변경O) 서해물과 백두산이 마르고 닳도록",
                            },
                            {
                                "is_changed": False,
                                "text_seq": 2,
                                "section_seq": 2,
                                "text_before": "(변경X) 하느님이 보우하사 우리나라 만세",
                                "text_after": "(변경X) 하느님이 보우하사 우리나라 만세",
                            }
                        ],
                    }
                ],
            }
        }


class DocApplyRequest(BaseModel):
    task_id: UUID
    has_merge_section: bool = False
    recipe_seq_list_selected: List[int]
    title: Optional[str] = None  # 신규 문서의 경우 제목 전달

class DocRenameRequest(BaseModel):
    title: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "변경된 문서 제목"
            }
        }

