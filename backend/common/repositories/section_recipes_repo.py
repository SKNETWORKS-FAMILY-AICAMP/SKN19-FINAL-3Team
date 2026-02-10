from typing import List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from common.models import SectionRecipe

class SectionRecipesRepository:
    """섹션 레시피 매핑 테이블(section_recipes) 작업 담당"""
    def __init__(self, db: AsyncSession):
        """DB 세션 초기화"""
        self.db = db

    # ------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------
    async def create_batch(self, recipes: List[SectionRecipe], auto_commit: bool = True) -> List[SectionRecipe]:
        """섹션 레시피 매핑 정보 일괄 생성"""
        self.db.add_all(recipes)
        
        if auto_commit:
            await self.db.commit()
            for record in recipes:
                await self.db.refresh(record)
        else:
            await self.db.flush()
            
        return recipes

    async def create_section_recipe(self, recipe_seq: int, text_seq: int, section_seq: int, coord: int, auto_commit: bool = True) -> SectionRecipe:
        """개별 섹션 레시피 매핑 생성"""
        record = SectionRecipe(
            recipe_seq=recipe_seq,
            text_seq=text_seq,
            section_seq=section_seq,
            coord=coord
        )
        self.db.add(record)
        
        if auto_commit:
            await self.db.commit()
            await self.db.refresh(record)
        else:
            await self.db.flush()
            
        return record

    # ------------------------------------------------------------
    # READ
    # ------------------------------------------------------------
    async def get_by_section_seq(self, section_seq: int) -> SectionRecipe:
        """section_seq로 섹션 레시피 매핑 조회"""
        stmt = select(SectionRecipe).where(SectionRecipe.section_seq == section_seq)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_section_seq_list(self, section_seq_list: List[int]) -> List[SectionRecipe]:
        """section_seq 리스트로 섹션 레시피 매핑 조회"""
        stmt = select(SectionRecipe).where(SectionRecipe.section_seq.in_(section_seq_list))
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_section_seq_in_recipes(self, section_seq: int, recipe_seqs: List[int]) -> List[SectionRecipe]:
        """section_seq에 해당하고 특정 recipe_seq들을 포함한 섹션 레시피 매핑 조회"""
        stmt = select(SectionRecipe).where(
            SectionRecipe.section_seq == section_seq,
            SectionRecipe.recipe_seq.in_(recipe_seqs)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    # recipe_seq를 가지고, 해당 레시피에 속한 section들의 리스트를 반환
    async def get_section_seqs_by_recipe_seq(self, recipe_seq: int) -> List[int]:
        stmt = select(SectionRecipe.section_seq).where(
            SectionRecipe.recipe_seq == recipe_seq
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()

    # ------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------

    # ------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------
    async def delete_by_recipe_seq(self, recipe_seq: int, auto_commit: bool = True) -> bool:
        """recipe_seq에 해당하는 모든 섹션 레시피 삭제"""
        stmt = delete(SectionRecipe).where(SectionRecipe.recipe_seq == recipe_seq)
        await self.db.execute(stmt)
        
        if auto_commit:
            await self.db.commit()
        else:
            await self.db.flush()
            
        return True

    # ------------------------------------------------------------
    # ETC
    # ------------------------------------------------------------

