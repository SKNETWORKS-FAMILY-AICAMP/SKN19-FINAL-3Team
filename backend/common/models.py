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

class CommonCode(Base):
    """시스템 공통 코드 관리"""
    __tablename__ = "common_codes"
    __table_args__ = (
        UniqueConstraint("code_group", "code_value", name="uq_group_value"),
        {"comment": "시스템 전반의 기준 정보를 관리하는 통합 코드 테이블"}
    )

    code_seq = Column(Integer, primary_key=True, index=True, comment="공통 코드 고유 식별자")
    code_group = Column(String(50), nullable=False, comment="코드 그룹 ID (DOC_TYPE, TEAM_ROLE 등)")
    code_value = Column(String(50), nullable=False, comment="실제 코드 값 (REQ_SPEC, TABLE 등)")
    code_name = Column(String(100), nullable=False, comment="화면 표시 명칭")
    is_use = Column(Boolean, default=True, comment="사용 여부")


class DocRecipe(Base):
    """문서 유형별 조립 규칙 정의"""
    __tablename__ = "doc_recipes"
    __table_args__ = {"comment": "문서 유형별 조립 규칙(레시피) 정의, 메인 테이블 "}

    recipe_seq = Column(Integer, primary_key=True, index=True)
    doc_type_code = Column(String(50), unique=True, nullable=False, comment="문서 유형 코드")
    recipe_value = Column(JSONB, nullable=False, comment="조립 규칙 상세 (JSON/Text)")
    title = Column(String(200), nullable=False, comment="문서 제목")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class DocSnapshot(Base):
    """문서 생성 결과 및 버저닝"""
    __tablename__ = "doc_snapshots"
    
    __table_args__ = (
        UniqueConstraint("team_seq", "doc_type_code", "snapshot_version", name="uq_team_doc_snapshot"),
        {"comment": "팀별/문서별 최종 생성된 결과물"}
    )
    
    snapshot_seq = Column(Integer, primary_key=True, index=True)
    team_seq = Column(Integer, ForeignKey("teams.team_seq"), nullable=True)
    doc_type_code = Column(String(50), nullable=False)
    is_official_copy = Column(Boolean, default=True, comment="TRUE: 자동갱신, FALSE: 편집본")
    snapshot_version = Column(Integer, default=1, comment="문서 저장 버전")
    content_text = Column(Text, nullable=False, comment="최종 렌더링 텍스트")
    last_editor_seq = Column(Integer, ForeignKey("users.user_seq"), nullable=True, comment="최종 수정자")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ModelLog(Base):
    """AI-사용자 상호작용 로그"""
    __tablename__ = "model_logs"
    __table_args__ = {"comment": "sLLM 파인튜닝을 위한 AI-사용자 상호작용 로그"}

    log_seq = Column(Integer, primary_key=True, index=True, comment="로그 고유 식별자 (Sequence)")
    operator_seq = Column(Integer, ForeignKey("users.user_seq"), nullable=True, comment="작업을 수행한 사용자 식별자")
    team_seq = Column(Integer, ForeignKey("teams.team_seq"), nullable=True, comment="작업이 수행된 팀 식별자")
    task_type_code = Column(String(20), nullable=False, comment="작업 단계 llm_task_type")
    task_id = Column(UUID(as_uuid=True), nullable=True, comment="task_id (uuid)")
    start_task_id = Column(UUID(as_uuid=True), nullable=True, comment="트랜잭션 연결을 위한 시작 task의 id")
    input_data = Column(JSONB, nullable=True, comment="AI 모델에 입력된 프롬프트 또는 데이터 (JSON)")
    ai_output = Column(JSONB, nullable=True, comment="AI 모델이 반환한 결과 데이터 (JSON)")
    user_decision = Column(JSONB, nullable=True, comment="사용자의 최종 수정/승인 데이터 (학습 레이블용)")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class OriginalText(Base):
    """가공 전 원본 텍스트 저장소"""
    __tablename__ = "original_text"

    text_seq = Column(Integer, primary_key=True, index=True)
    section_seq = Column(Integer, ForeignKey("sections.section_seq"), nullable=True, comment="해당 텍스트가 속하는 섹션")
    original_text = Column(Text, nullable=False, comment="가공 전 원본 텍스트")


class RefreshToken(Base):
    """인증 갱신 및 세션 관리"""
    __tablename__ = "refresh_tokens"
    __table_args__ = {"comment": "JWT 인증 갱신 및 사용자 세션/팀 컨텍스트 유지 관리"}

    token_seq = Column(Integer, primary_key=True, index=True)
    user_seq = Column(Integer, ForeignKey("users.user_seq"), nullable=True)
    current_team_seq = Column(Integer, ForeignKey("teams.team_seq"), nullable=True, comment="마지막 접속 팀 (재접속 시 Team Key 로드용)")
    token_value = Column(String(512), nullable=False, index=True, comment="Refresh Token 값 (Hash 저장 권장)")
    device_info = Column(String(255), nullable=True, comment="접속 기기/브라우저 정보")
    expires_at = Column(DateTime, nullable=False, comment="토큰 만료 일시")
    created_at = Column(DateTime, server_default=func.now())


class Section(Base):
    """지식 본문 및 벡터 데이터 관리"""
    __tablename__ = "sections"
    __table_args__ = {"comment": "RAG 검색을 위한 지식의 최소 단위 및 임베딩 저장소"}

    section_seq = Column(Integer, primary_key=True, index=True, comment="섹션 고유 식별자")
    tag = Column(JSONB, nullable=False, comment="연관 태그 식별자")

    # AI 처리 후 결과 (요약 + 벡터)
    essence = Column(Text, nullable=False, comment="LLM이 요약/정제한 핵심 지식 (Vector 임베딩 대상)")
    essence_vector = Column(Vector(768), nullable=True, comment="임베딩 벡터 데이터")
    origin_type_code = Column(String(50), nullable=False, comment="원본 데이터 형태 (TABLE, TEXT, IMAGE 등)")
    
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class SectionRecipe(Base):
    """섹션별 조립 순서 및 규칙 매핑"""
    __tablename__ = "section_recipes"

    section_coord_seq = Column(Integer, primary_key=True, index=True)
    section_seq = Column(Integer, ForeignKey("sections.section_seq"), nullable=True, comment="속한 섹션")
    text_seq = Column(Integer, ForeignKey("original_text.text_seq"), nullable=True, comment="사용할 텍스트")
    recipe_seq = Column(Integer, ForeignKey("doc_recipes.recipe_seq"), nullable=True, comment="섹션이 속한 레시피")
    coord = Column(Integer, comment="섹션이 들어갈 순서(위치)")


class SecureToken(Base):
    """민감 정보 토큰화 저장소"""
    __tablename__ = "secure_tokens"
    __table_args__ = {"comment": "민감 정보 보호를 위한 토큰화 저장소 (Token Vault)"}

    token_seq = Column(Integer, primary_key=True, index=True, comment="토큰 고유 번호")
    team_seq = Column(Integer, ForeignKey("teams.team_seq"), nullable=True, comment="암호화 키 소유 팀 (복호화 시 해당 팀의 키 필요)")
    token_text = Column(String(100), unique=True, nullable=False, comment="외부 노출용 토큰 (예: tk_x9z8...), 중복 불가")
    data_type = Column(String(50), nullable=False, comment="데이터 유형 (EMAIL, PHONE, RRN, CREDIT_CARD 등)")
    ciphertext = Column(Text, nullable=False, comment="암호화된 실제 데이터 (표준용어: ciphertext)")
    data_hash = Column(String(128), nullable=False, comment="검색 및 중복 확인을 위한 해시값 (SHA-256)")
    created_at = Column(DateTime, server_default=func.now())


class Tag(Base):
    """지식의 계층적 분류(카테고리/폴더)를 관리하는 태그 테이블"""
    __tablename__ = "tags"
    __table_args__ = {"comment": "지식의 계층적 분류(카테고리/폴더)를 관리하는 태그 테이블"}

    tag_seq = Column(Integer, primary_key=True, index=True, comment="태그 고유 식별자")
    tag_name = Column(String(255), nullable=False, comment="태그 명칭")
    depth = Column(Integer, comment="태그 계층 깊이")
    summary = Column(Text, comment="태그-요약 매칭용 텍스트")
    tag_vector = Column(Vector(768), comment="summary 임베딩 벡터 데이터")
    created_at = Column(DateTime, server_default=func.now())


class Team(Base):
    """프로젝트 및 팀 정보"""
    __tablename__ = "teams"
    __table_args__ = {"comment": "지식 자산을 공유하는 프로젝트/팀 단위"}

    team_seq = Column(Integer, primary_key=True, index=True, comment="팀 고유 식별자")
    team_name = Column(String(100), nullable=False, comment="팀 또는 프로젝트 명칭")
    created_at = Column(DateTime, server_default=func.now())


class TeamKey(Base):
    """팀 데이터 암호화 키 저장소"""
    __tablename__ = "team_keys"
    __table_args__ = {"comment": "팀 데이터 암호화/복호화를 위한 전용 키 저장소"}

    team_key_seq = Column(Integer, primary_key=True, index=True)
    team_seq = Column(Integer, ForeignKey("teams.team_seq"), unique=True, nullable=False, comment="대상 팀 식별자")
    encrypted_team_key = Column(Text, nullable=False, comment="Master Key로 암호화된 팀 전용 대칭키")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class TeamMember(Base):
    """팀 소속 멤버 및 역할 매핑"""
    __tablename__ = "team_members"
    __table_args__ = {"comment": "팀별 소속 멤버 및 역할 매핑 정보"}

    team_seq = Column(Integer, ForeignKey("teams.team_seq"), primary_key=True, comment="소속 팀 식별자")
    user_seq = Column(Integer, ForeignKey("users.user_seq"), primary_key=True, comment="소속 사용자 식별자")
    role_code = Column(String(50), nullable=False, comment="역할 (T_ADMIN, T_EDITOR, T_VIEWER)")


class User(Base):
    """시스템 사용자 계정 정보"""
    __tablename__ = "users"
    __table_args__ = {"comment": "시스템 사용자 계정 정보"}

    user_seq = Column(Integer, primary_key=True, index=True, comment="사용자 고유 식별자")
    display_name = Column(String(20), nullable=False, comment="사용자 표시명")
    username = Column(String(100), unique=True, nullable=False, comment="로그인 아이디 (OAuth2 username)")
    password = Column(Text, nullable=False, comment="암호화된 비밀번호")
    status_code = Column(String(20), default="ACTIVE", comment="계정 상태 (ACTIVE, SLEEP, QUIT)")
    created_at = Column(DateTime, server_default=func.now())

class DocRecipeMember(Base):
    """문서 레시피 접근 권한 매핑"""
    __tablename__ = "doc_recipe_members"
    __table_args__ = {"comment": "문서 레시피(doc_recipes)에 대한 사용자별 접근 권한 매핑"}

    recipe_seq = Column(
        Integer,
        ForeignKey("doc_recipes.recipe_seq", ondelete="CASCADE"),
        primary_key=True,
        comment="문서 레시피 식별자"
    )

    user_seq = Column(
        Integer,
        ForeignKey("users.user_seq", ondelete="CASCADE"),
        primary_key=True,
        comment="접근 권한을 가진 사용자 식별자"
    )

    role_code = Column(
        String(50),
        nullable=False,
        comment="레시피 권한 (R_ADMIN, R_EDITOR, R_VIEWER)"
    )

class DocLocal(Base):
    """문서 레시피 자동 저장 데이터"""
    __tablename__ = "doc_locals"
    __table_args__ = {
        "comment": "문서 레시피별 사용자 자동 저장(임시) 데이터"
    }

    recipe_seq = Column(
        Integer,
        ForeignKey("doc_recipes.recipe_seq", ondelete="CASCADE"),
        primary_key=True,
        comment="문서 레시피 식별자"
    )

    user_seq = Column(
        Integer,
        ForeignKey("users.user_seq", ondelete="CASCADE"),
        primary_key=True,
        comment="자동 저장 사용자 식별자"
    )

    text = Column(
        Text,
        nullable=False,
        comment="자동 저장된 문서 내용"
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="마지막 자동 저장 시각"
    )



# DB에 Patterns 저장할 테이블 없음. 나중에 생성해야 함
class Pattern(Base):
    """민감정보 식별 패턴"""
    __tablename__ = "patterns"
    __table_args__ = {
        "comment": "민감정보 식별 패턴"
    }
    pattern_seq = Column(Integer, primary_key=True, index=True)
    pattern_name = Column(String(255), nullable=False, comment="패턴 이름")
    regex_pattern = Column(String(255), nullable=False, comment="정규식 패턴")
    is_active = Column(Boolean, nullable=False, default=True, comment="활성화 여부")

# 기초 데이터
# ------------------------------------------------------------------
# INSERT INTO patterns (pattern_name, regex_pattern, is_active) VALUES
# ('RRN_PATTERN', '\b\d{6}-?[1-4]\d{6}\b', true),
# ('PHONE_NUM_PATTERN', '\b01[016789]-?\d{3,4}-?\d{4}\b', true),
# ('EMAIL_PATTERN', '\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', true),
# ('TOKEN_PATTERN', '\b(api[_-]?key|access[_-]?token|secret|bearer)\b\s*[:=]\s*[A-Za-z0-9\-_\.]{16,}', true),
# ('IP_PATTERN', '\b(?:\d{1,3}\.){3}\d{1,3}\b', true)
# ON CONFLICT (pattern_seq) DO NOTHING;

# -- 마이그레이션 결과 확인
# SELECT pattern_seq, pattern_name, regex_pattern, is_active 
# FROM patterns 
# ORDER BY pattern_seq;

# [문서 권한 관리] class DocRecipeMember 존재함
# [감사 로그] class ModelLog 존재함
# [사용자 관리] class User 존재함