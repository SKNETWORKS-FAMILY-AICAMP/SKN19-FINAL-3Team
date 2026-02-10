"""
Repository for doc_recipes table.
비즈니스 로직은 Service 계층에 두고, 여기서는 CRUD/조회만 담당한다.
"""

from typing import List, Optional, Any
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from common.models import DocRecipe


class DocRecipesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------
    async def create(self, recipe: DocRecipe) -> DocRecipe:
        """새 레시피 생성"""
        self.db.add(recipe)
        await self.db.commit()
        await self.db.refresh(recipe)
        return recipe

    async def create_doc_recipe(
        self,
        doc_type_code: str,
        title: str,
        recipe_value: Any,
        auto_commit: bool = True
    ) -> DocRecipe:
        """새 레시피 생성 (필드별 인자 전달)"""
        recipe = DocRecipe(
            doc_type_code=doc_type_code,
            title=title,
            recipe_value=recipe_value
        )
        self.db.add(recipe)
        
        if auto_commit:
            await self.db.commit()
            await self.db.refresh(recipe)
        else:
            await self.db.flush()
            
        return recipe

    # ------------------------------------------------------------
    # READ
    # ------------------------------------------------------------
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

    async def get_by_seqs(self, recipe_seq_list: List[int]) -> List[DocRecipe]:
        """recipe_seq 목록으로 여러 레시피 조회"""
        if not recipe_seq_list:
            return []
        stmt = select(DocRecipe).where(DocRecipe.recipe_seq.in_(recipe_seq_list))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    
    async def get_by_title(self, title: str) -> Optional[DocRecipe]:
        """제목으로 레시피 조회 (중복 체크용)"""
        stmt = select(DocRecipe).where(DocRecipe.title == title)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    # ------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------
    async def update_title(self, recipe_seq: int, title: str) -> bool:
        """문서 제목 수정"""
        stmt = (
            update(DocRecipe)
            .where(DocRecipe.recipe_seq == recipe_seq)
            .values(
                title=title,
                updated_at=datetime.now()
            )
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

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

    async def touch_recipe_value(self, recipe_seq: int, recipe_value: Any, auto_commit: bool = True) -> bool:
        """레시피의 조립 규칙 상세 정의를 torch로 변환하여 저장"""
        stmt = (
            update(DocRecipe)
            .where(DocRecipe.recipe_seq == recipe_seq)
            .values(recipe_value=recipe_value, updated_at=datetime.now())
        )
        result = await self.db.execute(stmt)
        
        if auto_commit:
            await self.db.commit()
        else:
            await self.db.flush()
            
        return result.rowcount > 0

    # ------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------
    async def delete_by_recipe_seq(self, recipe_seq: int, auto_commit: bool = True) -> bool:
        """recipe_seq로 doc_recipe 삭제"""
        from sqlalchemy import delete
        
        stmt = delete(DocRecipe).where(DocRecipe.recipe_seq == recipe_seq)
        result = await self.db.execute(stmt)
        
        if auto_commit:
            await self.db.commit()
        else:
            await self.db.flush()
        
        return result.rowcount > 0

    # ------------------------------------------------------------
    # ETC
    # ------------------------------------------------------------
        
