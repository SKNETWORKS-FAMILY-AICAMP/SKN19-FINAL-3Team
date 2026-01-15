"""
Repository for doc_recipes table.
비즈니스 로직은 Service 계층에 두고, 여기서는 CRUD/조회만 담당한다.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from common.models import DocRecipe


class DocRecipesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_latest(self) -> Optional[DocRecipe]:
        """가장 최근에 수정된 레시피 조회 (updated_at 기준 내림차순)"""
        stmt = (
            select(DocRecipe)
            .order_by(DocRecipe.updated_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def get_all(self) -> List[DocRecipe]:
        """모든 공통 코드를 그룹/코드값 정렬로 조회."""
        stmt = select(DocRecipe).order_by(DocRecipe.updated_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_seq(self, recipe_seq: int) -> Optional[DocRecipe]:
        """recipe_seq로 특정 레시피 조회"""
        stmt = select(DocRecipe).where(DocRecipe.recipe_seq == recipe_seq)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def touch_updated_at(self, recipe_seq: int) -> bool:
        """recipe의 updated_at을 현재 시간으로 갱신"""
        stmt = (
            update(DocRecipe)
            .where(DocRecipe.recipe_seq == recipe_seq)
            .values(updated_at=datetime.now())
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0
