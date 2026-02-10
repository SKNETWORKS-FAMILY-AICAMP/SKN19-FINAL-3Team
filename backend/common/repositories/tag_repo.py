"""
사용법 참고:

TagRepository는 태그 테이블에 대한 DB 조회 및 관리를 담당함.
"""

from typing import List, Any
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from common.models import Tag
from common.util.AI_API import GeminiApi


class TagRepository:
    """태그(카테고리) 정보를 관리하는 저장소."""

    def __init__(self, db: AsyncSession):
        """DB 세션을 초기화함."""
        self.db = db
        self.gemini_api = GeminiApi()

    async def _create_tag_vector(self, summary: str) -> list[int] :
        vector = await self.gemini_api.create_sentence_vector(summary)
        return vector
    
    # ------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------
    async def create_category(self, tag_name: str, depth: int, summary: str) -> int:
        """해당 태그를 생성하고, tag_seq를 반환"""

        tag_vector = await self._create_tag_vector(summary)
        print(tag_vector[0])
        tag = Tag(
            tag_name=tag_name,
            depth=depth,
            summary=summary,
            tag_vector=tag_vector,
        )

        self.db.add(tag)
        await self.db.commit()
        await self.db.refresh(tag)

        return tag.tag_seq


    # ------------------------------------------------------------
    # READ
    # ------------------------------------------------------------
    async def get_category_list(self) -> List[Tag]:
        """현재 DB에 존재하는 모든 카테고리(태그) 목록을 조회함."""
        stmt = select(Tag).order_by(Tag.tag_seq)
        
        result = await self.db.execute(stmt)
        
        return list(result.scalars().all())




    async def get_seqs_by_names(self, tag_names: List[str]) -> List[int]:
        """태그 이름 목록으로 태그 식별자(tag_seq) 목록을 조회함."""
        if not tag_names:
            return []
        
        stmt = select(Tag.tag_seq).where(Tag.tag_name.in_(tag_names))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def read_all_categories(self) -> List[Tag]:
        """모든 카테고리 정보를 조회"""
        stmt = select(Tag)
        result = await self.db.execute(stmt)
        return result.scalars().all()


    # ------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------
    async def update_category(self, tag_seq: int, tag_name: str, depth: int, summary: str):
        """수정된 태그 정보를 DB에 반영 (summary 변경 시 vector 재생성)"""
        # 현재 DB에서 tag_seq, tag_name은 unique 하지 않음
        # tag_seq만 unique하다고 가정했음

        stmt = select(Tag).where(Tag.tag_seq == tag_seq)
        result = await self.db.execute(stmt)
        result = result.scalar_one_or_none()
        if result is None:
            raise ValueError(f"태그 식별자 {tag_seq}에 해당하는 태그가 존재하지 않습니다.")

        if summary:
            if result.summary != summary:
                result.summary = summary
                try:
                    result.tag_vector = await self.gemini_api.create_sentence_vector(summary)
                except Exception as e:
                    raise ValueError(f"Gemini API로 태그 요약 벡터 생성 실패: {e}")
        
        if depth:
            if depth > 0 and depth < 6:
                result.depth = depth
            else:
                raise ValueError(f"태그 depth는 1 이상 5 이하이어야 합니다.: 입력받은 depth: {depth}")

        # 태그명은 duplicate 허용
        if tag_name:
            result.tag_name = tag_name

        await self.db.commit()
        await self.db.refresh(result)
        return result


    # ------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------
    async def delete_category(self, tag_seq: int):
        """해당 태그를 DB에서 삭제"""
        stmt = delete(Tag).where(Tag.tag_seq == tag_seq)
        await self.db.execute(stmt)
        await self.db.commit()
    

    # ------------------------------------------------------------
    # ETC
    # ------------------------------------------------------------