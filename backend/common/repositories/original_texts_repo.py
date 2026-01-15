"""
Repository for original_texts table.
비즈니스 로직은 Service 계층에 두고, 여기서는 CRUD/조회만 담당한다.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from common.models import OriginalText, Section, SectionRecipe


class OriginalTextsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def section_exists(self, section_seq: int) -> bool:
        """Section 존재 여부 확인"""
        stmt = select(Section).where(Section.section_seq == section_seq)
        result = await self.db.execute(stmt)
        return result.scalars().first() is not None

    async def get_by_section(self, section_seq: int) -> List[OriginalText]:
        """특정 section에 속한 original_texts 목록 조회"""
        stmt = (
            select(OriginalText)
            .where(OriginalText.section_seq == section_seq)
            .order_by(OriginalText.text_seq)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_text_seq(self, text_seq: int) -> Optional[OriginalText]:
        """특정 text_seq로 original_text 조회"""
        stmt = select(OriginalText).where(OriginalText.text_seq == text_seq)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_batch(self, section_seq: int, texts: List[str]) -> List[OriginalText]:
        """여러 original_texts 일괄 생성"""
        records = [
            OriginalText(section_seq=section_seq, original_text=text)
            for text in texts
        ]
        self.db.add_all(records)
        await self.db.commit()
        for record in records:
            await self.db.refresh(record)
        return records

    async def update_text(self, text_seq: int, new_text: str) -> Optional[OriginalText]:
        """특정 text_seq의 텍스트 업데이트"""
        stmt = select(OriginalText).where(OriginalText.text_seq == text_seq)
        result = await self.db.execute(stmt)
        record = result.scalars().first()

        if not record:
            return None

        record.original_text = new_text
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def delete_by_seq(self, text_seq: int) -> bool:
        """특정 text_seq 삭제"""
        stmt = select(OriginalText).where(OriginalText.text_seq == text_seq)
        result = await self.db.execute(stmt)
        record = result.scalars().first()

        if not record:
            return False

        await self.db.delete(record)
        await self.db.commit()
        return True

    async def delete_by_section(self, section_seq: int) -> int:
        """특정 section의 모든 original_texts 삭제"""
        stmt = select(OriginalText).where(OriginalText.section_seq == section_seq)
        result = await self.db.execute(stmt)
        records = result.scalars().all()

        count = 0
        for record in records:
            await self.db.delete(record)
            count += 1

        await self.db.commit()
        return count

    async def get_recipe_seq_by_section(self, section_seq: int) -> Optional[int]:
        """특정 section이 사용하는 recipe_seq 조회"""
        stmt = (
            select(SectionRecipe.recipe_seq)
            .where(SectionRecipe.section_seq == section_seq)
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar()
