"""
사용법 참고:

Repository는 공통 코드에 대한 DB 조회/저장을 전담한다. 비즈니스 판단이나 데이터 가공은 Service에 둔다.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from common.models import CommonCode


class CommonCodeRepository:
    """공통 코드 테이블을 조회·생성하는 저장소."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, code_group: str, code_value: str, code_name: str, is_use: bool = True) -> CommonCode:
        """새 공통 코드 레코드를 추가하고 커밋."""
        record = CommonCode(
            code_group=code_group,
            code_value=code_value,
            code_name=code_name,
            is_use=is_use,
        )
        self.db.add(record)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise
        await self.db.refresh(record)
        return record

    async def get_by_group(self, code_group: str) -> List[CommonCode]:
        """특정 그룹에 속한 코드 목록을 그룹 내 정렬로 조회."""
        stmt = select(CommonCode).where(CommonCode.code_group == code_group).order_by(CommonCode.code_value)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_one(self, code_group: str, code_value: str) -> Optional[CommonCode]:
        """그룹과 코드값으로 단일 공통 코드를 조회."""
        stmt = select(CommonCode).where(
            CommonCode.code_group == code_group,
            CommonCode.code_value == code_value,
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_all(self) -> List[CommonCode]:
        """모든 공통 코드를 그룹/코드값 정렬로 조회."""
        stmt = select(CommonCode).order_by(CommonCode.code_group, CommonCode.code_value)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
