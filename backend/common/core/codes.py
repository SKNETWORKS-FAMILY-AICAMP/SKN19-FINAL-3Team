"""
공통 코드와 연동되는 Enum 정의.
DB의 common_codes 테이블과 값이 일치해야 한다.
"""
from enum import Enum


class CodeGroup(str, Enum):
    """공통 코드 그룹 상수."""
    LLM_TASK_TYPE = "LLM_TASK_TYPE"
    LLM_TASK_STATUS = "LLM_TASK_STATUS"


class LlmTaskType(str, Enum):
    """LLM 작업 유형 (common_codes.code_value)."""
    DOC_INDEX = "DOC_INDEX" # 문서 분할 + 문서 색인
    DOC_UPDATE = "DOC_UPDATE"


class LlmTaskStatus(str, Enum):
    """LLM 작업 상태 (common_codes.code_value)."""
    PENDING = "PENDING"      # 등록됨
    PROCESSING = "PROCESSING"  # 처리중
    COMPLETE = "COMPLETE"    # 완료
    ERROR = "ERROR"          # 오류

