"""
Repository for original_texts table.
비즈니스 로직은 Service 계층에 두고, 여기서는 CRUD/조회만 담당한다.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from common.models import OriginalText, Section, SectionRecipe, DocRecipe


class OriginalTextsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------
    async def create(self, section_seq: int, original_text: str, auto_commit: bool = True) -> OriginalText:
        """단일 original_text 생성"""
        record = OriginalText(
            section_seq=section_seq,
            original_text=original_text
        )
        self.db.add(record)
        
        if auto_commit:
            await self.db.commit()
            await self.db.refresh(record)
        else:
            await self.db.flush()
            
        return record

    async def create_batch(self, section_seq: int, texts: List[str], auto_commit: bool = True) -> List[OriginalText]:
        """여러 original_texts 일괄 생성"""
        records = [
            OriginalText(section_seq=section_seq, original_text=text)
            for text in texts
        ]
        self.db.add_all(records)
        
        if auto_commit:
            await self.db.commit()
            for record in records:
                await self.db.refresh(record)
        else:
            await self.db.flush()
            
        return records

    # ------------------------------------------------------------
    # READ
    # ------------------------------------------------------------
    
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

    async def section_exists(self, section_seq: int) -> bool:
        """Section 존재 여부 확인"""
        stmt = select(Section).where(Section.section_seq == section_seq)
        result = await self.db.execute(stmt)
        return result.scalars().first() is not None

    async def get_original_texts(
        self, 
        text_seqs: Optional[List[int]] = None, 
        section_seqs: Optional[List[int]] = None
    ) -> List[OriginalText]:
        """
        text_seqs나 section_seqs 중 하나라도 있으면 조회, 
        둘 다 없으면 빈 리스트 반환
        """
        
        # 둘 다 조건이 없으면(None이거나 빈 리스트) 바로 종료함
        # DB 쿼리 실행 안 함
        if not text_seqs and not section_seqs:
            return []

        stmt = select(OriginalText)

        # text_seqs가 있을 때만 WHERE 절에 추가 (AND 조건)
        # text_seq IN (...)
        if text_seqs:
            stmt = stmt.where(OriginalText.text_seq.in_(text_seqs))

        # section_seqs가 있을 때만 WHERE 절에 추가 (AND 조건)
        # section_seq IN (...)
        if section_seqs:
            stmt = stmt.where(OriginalText.section_seq.in_(section_seqs))
        
        # 보기 좋게 정렬 (필요시)
        stmt = stmt.order_by(OriginalText.text_seq)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_recipe_seq_by_section(self, section_seq: int) -> Optional[int]:
        """특정 section이 사용하는 recipe_seq 조회"""
        stmt = (
            select(SectionRecipe.recipe_seq)
            .where(SectionRecipe.section_seq == section_seq)
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar()

    async def get_section_seq_by_text_seq(self, text_seq: int) -> Optional[int]:
        """text_seq로 section_seq 조회"""
        stmt = select(OriginalText.section_seq).where(OriginalText.text_seq == text_seq)
        result = await self.db.execute(stmt)
        return result.scalar()

    async def get_by_stripped_text(self, text: str) -> Optional[OriginalText]:
        """
        텍스트로 OriginalText 레코드 조회
        앞뒤 개행 문자, 띄어쓰기를 제거한 후 비교
        """
        # 입력 텍스트 정규화 (앞뒤 공백/개행 제거)
        normalized_text = text.strip()
        
        # 모든 OriginalText 레코드 조회
        stmt = select(OriginalText)
        result = await self.db.execute(stmt)
        all_texts = result.scalars().all()
        
        # 정규화된 텍스트와 일치하는 레코드 찾기
        for record in all_texts:
            if record.original_text and record.original_text.strip() == normalized_text:
                return record
        
        return None

    # 해당 텍스트가 본문에 포함된 text_seq 리스트 반환
    async def get_text_seq_by_keyword(self, keyword: str) -> list[int] :
        stmt = (
            select(
                OriginalText.text_seq,
                OriginalText.original_text,
            )
            .where(OriginalText.original_text.ilike(f"%{keyword}%"))
        )


        rows = (await self.db.execute(stmt)).mappings().all()

        return rows

    # ------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------
    async def update_text(self, text_seq: int, new_text: str, auto_commit: bool = True) -> Optional[OriginalText]:
        """특정 text_seq의 텍스트 업데이트"""
        stmt = select(OriginalText).where(OriginalText.text_seq == text_seq)
        result = await self.db.execute(stmt)
        record = result.scalars().first()

        if not record:
            return None

        record.original_text = new_text

        now = datetime.utcnow()

        if record.section_seq:
            await self.db.execute(
                update(Section)
                .where(Section.section_seq == record.section_seq)
                .values(updated_at=now)
            )

            recipe_seq = await self.get_recipe_seq_by_section(record.section_seq)

            if recipe_seq:
                await self.db.execute(
                    update(DocRecipe)
                    .where(DocRecipe.recipe_seq == recipe_seq)
                    .values(updated_at=now)
                )

        
        if auto_commit:
            await self.db.commit()
            await self.db.refresh(record)
        else:
            await self.db.flush()
            
        return record


    # ------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------
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

    async def delete_by_recipe_seq(self, recipe_seq: int, auto_commit: bool = True) -> bool:
        """recipe_seq에 해당하는 모든 original_texts 삭제"""
        from sqlalchemy import delete
        
        # section_recipes를 통해 text_seq 목록을 가져온 후 삭제
        stmt = (
            delete(OriginalText)
            .where(
                OriginalText.text_seq.in_(
                    select(SectionRecipe.text_seq)
                    .where(SectionRecipe.recipe_seq == recipe_seq)
                )
            )
        )
        result = await self.db.execute(stmt)
        
        if auto_commit:
            await self.db.commit()
        else:
            await self.db.flush()
        
        return result.rowcount > 0

    async def delete_orphaned_texts(self, auto_commit: bool = True) -> int:
        """연결이 끊어진(어떤 섹션 레시피에서도 참조하지 않는) original_texts 삭제"""
        from sqlalchemy import delete
        
        # DELETE FROM original_texts WHERE text_seq NOT IN (SELECT text_seq FROM section_recipes)
        # subquery for text_seqs in section_recipes
        used_text_seqs = select(SectionRecipe.text_seq)
        
        stmt = (
            delete(OriginalText)
            .where(
                OriginalText.text_seq.notin_(used_text_seqs)
            )
        )
        
        result = await self.db.execute(stmt)
        
        if auto_commit:
            await self.db.commit()
        else:
            await self.db.flush()
            
        return result.rowcount

    # ------------------------------------------------------------
    # ETC
    # ------------------------------------------------------------