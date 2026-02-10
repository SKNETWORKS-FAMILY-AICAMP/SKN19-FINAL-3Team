"""
공통 코드와 연동되는 Enum 정의.
DB의 common_codes 테이블과 값이 일치해야 한다.
"""
from enum import Enum


class CodeGroup(str, Enum):
    """공통 코드 그룹 상수."""
    LLM_TASK_TYPE = "LLM_TASK_TYPE"
    LLM_TASK_STATUS = "LLM_TASK_STATUS"
    DOC_RECIPE_ROLE = "DOC_RECIPE_ROLE"


class LlmTaskType(str, Enum):
    """LLM 작업 유형 (common_codes.code_value)."""
    DOC_INDEX = "DOC_INDEX" # 문서 분할 + 문서 색인
    DOC_UPDATE = "DOC_UPDATE"
    MERGE_PROP = 'MERGE_PROP'


class LlmTaskStatus(str, Enum):
    """LLM 작업 상태 (common_codes.code_value)."""
    PENDING = "PENDING"      # 등록됨
    PROCESSING = "PROCESSING"  # 처리중
    COMPLETED = "COMPLETED"    # 완료
    ERROR = "ERROR"          # 오류


class MergeProposalType(str, Enum):
    """병합 제안 유형 (Proposal Type)."""
    ALL_EXIST = "ALL_EXIST"                     # 모두 존재
    ALL_NEW = "ALL_NEW"                         # 모두 신규
    PROPOSAL_REQUIRED = "PROPOSAL_REQUIRED"     # 제안 필요 (Mixed)
    NO_PROPOSAL = "NO_PROPOSAL"                 # 병합 제안 없음

class MergeActionType(str, Enum):
    """병합 유형 (Action Type)."""
    SKIP = "SKIP"                       # 100% 유사함 = 아무것도 하지 않음
    LINK_SECTION = "LINK_SECTION"       # 임계치 LEVEL 1 (초기:95%) 같다고 판단 = 섹션 요약 기존에 연결, 섹션 원본 추가
    MERGE_SECTION = "MERGE_SECTION"     # 임계치 LEVEL 2 (초기:80%) 유사하다고 판단 = 섹션 요약 변경, 섹션 원본 추가
    CREATE_NEW = "CREATE_NEW"           # 임계치 LEVEL 2 미만, 신규라고 판단
    UNKNOWN = "UNKNOWN"                 # 알 수 없음
    

class DocRecipeRole(str, Enum):
    """문서 레시피 권한 역할 (doc_recipe_members.role_code)."""
    R_ADMIN = "R_ADMIN"      # 관리자 (모든 권한)
    R_EDITOR = "R_EDITOR"    # 편집자 (편집, 삭제 가능)
    R_VIEWER = "R_VIEWER"    # 조회자 (읽기만 가능)
