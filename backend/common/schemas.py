"""
사용법 참고:

schemas.py는 요청/응답 DTO를 정의한다. 검증/직렬화 스펙만 담고,
비즈니스 로직이나 DB 접근은 포함하지 않는다.
"""

from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

from common.core.codes import LlmTaskStatus, LlmTaskType
from pydantic import BaseModel


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

class ProposalSimilarSection(BaseModel):
    text_seq: int
    section_seq: int
    origin_text: str
    merge_suggestion: str

class ProposalSection(BaseModel):
    input_text: str
    similar_section: Optional[ProposalSimilarSection] = None

class DocProposalResponse(BaseModel):
    sections: List[ProposalSection]

    class Config:
        json_schema_extra = {
            "example": {
                "sections": [
                    {
                        "input_text": "# 협업 문서 편집 플랫폼 – 내부 논의용 정리\n\n",
                        "similar_section": {
                            "text_seq": 1,  # original_text 테이블의 값
                            "section_seq": 1,
                            "origin_text": " 협업 문서 편집 플랫폼 (A.J.C) 기획서\n\n",
                            "merge_suggestion": "(제안) 협업 문서 편집 플랫폼 (A.J.C) 기획서\n\n" # 병합 제안 생성된 값
                        }
                    },
                    {
                        "input_text": "제안이 없이 신규인 경우"
                    }
                ]
            }
        }


# [Document Update] 병합 업데이트 요청
class DocUpdateRequestItem(BaseModel):
    text_seq: int
    section_seq: int
    is_merge: bool
    input_text: str
    origin_text: str
    merge_suggestion: str

class DocUpdateRequest(BaseModel):
    sections: List[DocUpdateRequestItem]

    class Config:
        json_schema_extra = {
            "example": {
                "sections": [
                    {
                        "text_seq": 1,
                        "section_seq": 1,
                        "is_merge": True,
                        "input_text": "# 협업 문서 편집 플랫폼 – 내부 논의용 정리\n\n",
                        "origin_text": " 협업 문서 편집 플랫폼 (A.J.C) 기획서\n\n",
                        "merge_suggestion": "(제안) 협업 문서 편집 플랫폼 (A.J.C) 기획서\n\n"
                    }
                ]
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
                "task_id": "650e8400-e29b-41d4-a716-446655440001",
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
