"""
사용법 참고:

models.py는 SQLAlchemy ORM 모델을 정의한다. 테이블/컬럼 구조만 기술하고,
비즈니스 로직은 Service, 쿼리는 Repository에 둔다.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID
from pgvector.sqlalchemy import Vector
from common.core.database import Base

# db 구조

# (1) 공통 및 사용자
class User(Base):
    __tablename__ = "users"
    user_seq = Column(Integer, primary_key=True, index=True, comment="사용자 고유 식별자")
    user_nm = Column(String(20), nullable=False, comment="사용자 실명")
    login_id = Column(String(100), unique=True, nullable=False, comment="로그인 아이디")
    login_pwd = Column(Text, nullable=False, comment="암호화된 비밀번호")
    status_code = Column(String(20), default="ACTIVE", comment="계정 상태 (ACTIVE, SLEEP, QUIT)")
    created_at = Column(DateTime, server_default=func.now())

class Team(Base):
    __tablename__ = "teams"
    team_seq = Column(Integer, primary_key=True, index=True, comment="팀 고유 식별자")
    team_name = Column(String(100), nullable=False, comment="팀 또는 프로젝트 명칭")
    created_at = Column(DateTime, server_default=func.now())

class TeamMember(Base):
    __tablename__ = "team_members"
    team_seq = Column(Integer, ForeignKey("teams.team_seq"), primary_key=True)
    user_seq = Column(Integer, ForeignKey("users.user_seq"), primary_key=True)
    role_code = Column(String(50), nullable=False, comment="역할 (T_ADMIN, T_EDITOR, T_VIEWER)")
    joined_at = Column(DateTime, server_default=func.now())

class TeamKey(Base):
    __tablename__ = "team_keys"
    team_key_seq = Column(Integer, primary_key=True, index=True)
    team_seq = Column(Integer, ForeignKey("teams.team_seq"), unique=True, nullable=False)
    encrypted_team_key = Column(Text, nullable=False, comment="Master Key로 암호화된 팀 전용 대칭키")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

# (2) 지식 자산 (Index & Section)
class Index(Base):
    __tablename__ = "indices"
    index_seq = Column(Integer, primary_key=True, index=True, comment="색인 고유 식별자")
    team_seq = Column(Integer, ForeignKey("teams.team_seq"), nullable=True)
    parent_seq = Column(Integer, ForeignKey("indices.index_seq"), nullable=True)
    index_name = Column(String(255), nullable=False, comment="색인 명칭")
    index_path = Column(Text, nullable=False, comment="검색 최적화용 경로")
    depth = Column(Integer, comment="색인 깊이")
    created_at = Column(DateTime, server_default=func.now())

class Section(Base):
    __tablename__ = "sections"

    section_seq = Column(Integer, primary_key=True, index=True, comment="섹션 고유 식별자")
    index_seq = Column(Integer, ForeignKey("indices.index_seq"), nullable=True)

    # AI 처리 후 결과 (요약 + 벡터)
    essence = Column(Text, nullable=False, comment="LLM 정제 핵심 지식 (RAG용)")
    essence_vector = Column(Vector(1535), nullable=True, comment="핵심 지식 벡터")
    origin_type_code = Column(String(50), nullable=False, comment="데이터 형태 (TABLE, TEXT 등)")
    
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class OriginalText(Base):
    __tablename__ = "original_text"

    text_seq = Column(Integer, primary_key=True, index=True)
    section_seq = Column(Integer, ForeignKey("sections.section_seq"), nullable=True)
    original_text = Column(Text, nullable=False, comment="가공 전 원본 텍스트")


class DocRecipe(Base):
    __tablename__ = "doc_recipes"

    recipe_seq = Column(Integer, primary_key=True, index=True)
    doc_type_code = Column(String(50), unique=True, nullable=False, comment="문서 유형 코드")
    recipe_value = Column(Text, nullable=False, comment="조립 규칙 상세 (JSON/Text)")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SectionRecipe(Base):
    __tablename__ = "section_recipes"

    section_coord_seq = Column(Integer, primary_key=True, index=True)
    section_seq = Column(Integer, ForeignKey("sections.section_seq"), nullable=True)
    text_seq = Column(Integer, ForeignKey("original_text.text_seq"), nullable=True)
    recipe_seq = Column(Integer, ForeignKey("doc_recipes.recipe_seq"), nullable=True)
    coord = Column(Integer, comment="섹션이 들어갈 순서(위치)")


class DocSnapshot(Base):
    __tablename__ = "doc_snapshots"
    
    snapshot_seq = Column(Integer, primary_key=True, index=True)
    team_seq = Column(Integer, ForeignKey("teams.team_seq"), nullable=True)
    doc_type_code = Column(String(50), nullable=False)
    is_official_copy = Column(Boolean, default=True, comment="TRUE: 자동갱신, FALSE: 편집본")
    snapshot_version = Column(Integer, default=1, comment="문서 저장 버전")
    content_text = Column(Text, nullable=False, comment="최종 렌더링 텍스트")
    last_editor_seq = Column(Integer, ForeignKey("users.user_seq"), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())  
    
    __table_args__ = (UniqueConstraint("team_seq", "doc_type_code", name="uq_team_doc_type"),)


# (3) 공통 코드
class CommonCode(Base):
    __tablename__ = "common_codes"
    __table_args__ = (UniqueConstraint("code_group", "code_value", name="uq_group_value"),)

    code_seq = Column(Integer, primary_key=True, index=True, comment="공통 코드 고유 식별자")
    code_group = Column(String(50), nullable=False, comment="코드 그룹 ID (DOC_TYPE, TEAM_ROLE 등)")
    code_value = Column(String(50), nullable=False, comment="실제 코드 값 (REQ_SPEC, TABLE 등)")
    code_name = Column(String(100), nullable=False, comment="화면 표시 명칭")
    is_use = Column(Boolean, default=True, comment="사용 여부")


# (4) 모델 로그 (AI-사용자 상호작용 기록)
class ModelLog(Base):
    __tablename__ = "model_logs"
    __table_args__ = {"comment": "sLLM 파인튜닝을 위한 AI-사용자 상호작용 로그"}

    log_seq = Column(Integer, primary_key=True, index=True, comment="로그 고유 식별자 (Sequence)")
    operator_seq = Column(Integer, ForeignKey("users.user_seq"), nullable=True, comment="작업을 수행한 사용자 식별자")
    team_seq = Column(Integer, ForeignKey("teams.team_seq"), nullable=True, comment="작업이 수행된 팀 식별자")
    task_type_code = Column(String(50), nullable=False, comment="작업 유형 common_code code_group llm_task_type")
    task_id = Column(UUID(as_uuid=True), nullable=True, comment="task_id (uuid)")
    input_data = Column(JSONB, nullable=True, comment="AI 모델에 입력된 프롬프트 또는 데이터 (JSON)")
    ai_output = Column(JSONB, nullable=True, comment="AI 모델이 반환한 결과 데이터 (JSON)")
    user_decision = Column(JSONB, nullable=True, comment="사용자의 최종 수정/승인 데이터 (학습 레이블용)")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


