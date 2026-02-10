from typing import Optional
from sqlalchemy import select, update, text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from common.models import DocLocal

class DocLocalRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------
    # CREATE / UPSERT
    # ------------------------------------------------------------
    async def upsert(
        self,
        recipe_seq: int,
        user_seq: int,
        text: str,
        auto_commit: bool = True,
    ) -> None:
        """
        로컬 자동 저장 생성 또는 갱신
        (recipe_seq + user_seq 기준 UPSERT)
        """
        stmt = sql_text("""
        INSERT INTO doc_locals (recipe_seq, user_seq, text)
        VALUES (:recipe_seq, :user_seq, :text)
        ON CONFLICT (recipe_seq, user_seq)
        DO UPDATE SET
            text = EXCLUDED.text,
            updated_at = now()
        """)
        await self.db.execute(
            stmt,
            {
                "recipe_seq": recipe_seq,
                "user_seq": user_seq,
                "text": text,
            },
        )

        if auto_commit:
            await self.db.commit()
        else:
            await self.db.flush()

    # ------------------------------------------------------------
    # READ
    # ------------------------------------------------------------
    async def get(
        self,
        recipe_seq: int,
        user_seq: int,
    ) -> Optional[str]:
        """특정 레시피 + 사용자 로컬 데이터 조회"""
        stmt = (
            select(DocLocal.text)
            .where(
                DocLocal.recipe_seq == recipe_seq,
                DocLocal.user_seq == user_seq,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar()

    async def get_full(
        self,
        recipe_seq: int,
        user_seq: int,
    ) -> Optional[DocLocal]:
        """로컬 데이터 전체 객체 조회"""
        stmt = (
            select(DocLocal)
            .where(
                DocLocal.recipe_seq == recipe_seq,
                DocLocal.user_seq == user_seq,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    # ------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------
    async def touch_updated_at(
        self,
        recipe_seq: int,
        user_seq: int,
    ) -> bool:
        """로컬 데이터의 updated_at만 갱신"""
        stmt = (
            update(DocLocal)
            .where(
                DocLocal.recipe_seq == recipe_seq,
                DocLocal.user_seq == user_seq,
            )
            .values(updated_at=datetime.now())
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    # ------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------
    async def delete(
        self,
        recipe_seq: int,
        user_seq: int,
    ) -> bool:
        """특정 로컬 자동 저장 데이터 삭제"""
        stmt = (
            DocLocal.__table__
            .delete()
            .where(
                DocLocal.recipe_seq == recipe_seq,
                DocLocal.user_seq == user_seq,
            )
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0
