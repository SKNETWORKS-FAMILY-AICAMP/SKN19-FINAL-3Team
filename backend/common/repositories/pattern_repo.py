from typing import Optional
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from common.models import Pattern

# 아직 Patterns 저장할 테이블 없음. 생성해야 함
# class Pattern(Base):
#     """민감정보 식별 패턴"""
#     __tablename__ = "patterns"
#     __table_args__ = {
#         "comment": "민감정보 식별 패턴"
#     }
#     pattern_name = Column(String(255), primary_key=True, nullable=False, comment="패턴 이름")
#     regex_pattern = Column(String(255), nullable=False, comment="정규식 패턴")
#     is_active = Column(Boolean, nullable=False, default=True, comment="활성화 여부")



class PatternRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------
    async def create_pattern(self, pattern: Pattern) -> Pattern:
        self.db.add(pattern)
        await self.db.commit()
        await self.db.refresh(pattern)
        return pattern

    # ------------------------------------------------------------
    # READ
    # ------------------------------------------------------------
    async def read_all_patterns(self) -> list[Pattern]:
        query = select(Pattern)
        result = await self.db.execute(query)
        return result.scalars().all()

    # ------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------
    async def update_pattern(self, pattern: Pattern) -> Pattern:
        query = select(Pattern).where(Pattern.pattern_seq == pattern.pattern_seq)
        result = await self.db.execute(query)
        existing_pattern = result.scalars().first()
        if existing_pattern:
            existing_pattern.pattern_name = pattern.pattern_name
            existing_pattern.regex_pattern = pattern.regex_pattern
            existing_pattern.is_active = pattern.is_active
            await self.db.commit()
            await self.db.refresh(existing_pattern)
        return existing_pattern

    # ------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------
    async def delete_pattern(self, pattern: Pattern) -> Pattern:
        query = select(Pattern).where(Pattern.pattern_seq == pattern.pattern_seq)
        result = await self.db.execute(query)
        existing_pattern = result.scalars().first()
        if existing_pattern:
            await self.db.delete(existing_pattern)
            await self.db.commit()
        return existing_pattern

    # ------------------------------------------------------------
    # ETC
    # ------------------------------------------------------------
