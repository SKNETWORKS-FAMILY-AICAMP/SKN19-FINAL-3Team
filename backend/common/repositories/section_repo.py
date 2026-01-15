"""
Repository for sections table.
비즈니스 로직은 Service 계층에 두고, 여기서는 CRUD/조회만 담당한다.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from common.models import Section
from pgvector.sqlalchemy import Vector
import numpy as np


class SectionRepository:
    """섹션 테이블을 조회·생성하는 저장소."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_section(
        self,
        index_seq: Optional[int],
        origin_type_code: str,
        essence: str = "",
        essence_vector: Optional[List[float]] = None,
    ) -> Section:
        """새 섹션 레코드를 추가하고 커밋."""
        record = Section(
            index_seq=index_seq,
            origin_type_code=origin_type_code,
            essence=essence if essence else "",
            essence_vector=np.array(essence_vector) if essence_vector else None,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def find_similar_sections(
        self, query_vector: List[float], k: int = 5
    ) -> List[Section]:
        """주어진 벡터와 가장 유사한 k개의 섹션을 검색합니다."""
        # pgvector의 벡터 유사도 검색 연산자 (cosine_distance) 사용
        # 이 연산자는 cosine distance를 계산하므로, ORDER BY로 오름차순 정렬하여 가장 유사한 결과를 얻음.
        # 즉, 0에 가까울수록 유사함.

        # essence_vector가 NULL이 아닌 레코드만 대상으로 함
        stmt = (
            select(Section)
            .where(Section.essence_vector.isnot(None))
            .order_by(Section.essence_vector.cosine_distance(query_vector))
            .limit(k)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_section_by_id(self, section_seq: int) -> Optional[Section]:
        """ID로 섹션 조회."""
        stmt = select(Section).where(Section.section_seq == section_seq)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_sections_by_index_seq(self, index_seq: int) -> List[Section]:
        """인덱스 ID로 모든 섹션 조회."""
        stmt = select(Section).where(Section.index_seq == index_seq)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
