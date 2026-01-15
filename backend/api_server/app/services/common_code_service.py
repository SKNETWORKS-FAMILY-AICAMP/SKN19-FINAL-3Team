"""
사용법 참고:

Service는 공통 코드 관련 비즈니스 규칙을 처리하고 Repository에 저장/조회 요청을 위임한다.
라우터는 Service만 호출해 로직을 수행한다.
"""

from sqlalchemy.exc import IntegrityError
from common.repositories.common_code_repo import CommonCodeRepository
from common.schemas import CommonCodeCreate


class CommonCodeService:
    """공통 코드 CRUD 흐름을 제공하는 서비스."""

    def __init__(self, repo: CommonCodeRepository):
        self.repo = repo

    async def register(self, payload: CommonCodeCreate):
        """새 공통 코드를 등록하고 중복이면 사용자 친화 에러를 반환."""
        try:
            return await self.repo.create(
                code_group=payload.code_group,
                code_value=payload.code_value,
                code_name=payload.code_name,
                is_use=payload.is_use,
            )
        except IntegrityError:
            # (group, value) unique constraint 위반 시 사용자 친화 에러를 던짐
            raise ValueError("이미 존재하는 코드입니다: 같은 group/value 조합이 있습니다.")

    async def list_by_group(self, code_group: str):
        """그룹에 속한 공통 코드 목록을 조회."""
        return await self.repo.get_by_group(code_group)

    async def get_one(self, code_group: str, code_value: str):
        """그룹/값으로 단일 공통 코드를 조회."""
        return await self.repo.get_one(code_group, code_value)

    async def list_all(self):
        """전체 공통 코드를 조회."""
        return await self.repo.get_all()
