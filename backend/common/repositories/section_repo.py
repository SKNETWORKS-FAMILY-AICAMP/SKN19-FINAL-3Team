"""
Repository for sections table.
비즈니스 로직은 Service 계층에 두고, 여기서는 CRUD/조회만 담당한다.
"""

from typing import List, Optional, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from common.models import Section
from pgvector.sqlalchemy import Vector
import numpy as np


class SectionRepository:
    """섹션 테이블을 조회·생성하는 저장소."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------
    async def create_section(
        self,
        tag: Any,
        origin_type_code: str,
        essence: str = "",
        essence_vector: Optional[List[float]] = None,
        auto_commit: bool = True,
    ) -> Section:
        """새 섹션 레코드를 추가하고 커밋."""
        record = Section(
            tag=tag,
            origin_type_code=origin_type_code,
            essence=essence if essence else "",
            essence_vector=np.array(essence_vector) if essence_vector else None,
        )
        self.db.add(record)
        
        if auto_commit:
            await self.db.commit()
            await self.db.refresh(record)
        else:
            await self.db.flush()
            # flush만 해도 PK는 생성됨
            
        return record

    # ------------------------------------------------------------
    # READ
    # ------------------------------------------------------------
    async def find_similar_sections(
        self,
        query : str,
        query_vector: List[float],
        k: int = 5,
        section_seq_list: Optional[List[int]] = None,
    ) -> List[Section]:
        """주어진 벡터와 가장 유사한 k개의 섹션을 검색합니다."""
        # pgvector의 벡터 유사도 검색 연산자 (cosine_distance) 사용
        # 이 연산자는 cosine distance를 계산하므로, ORDER BY로 오름차순 정렬하여 가장 유사한 결과를 얻음.
        # 즉, 0에 가까울수록 유사함.

        # essence_vector가 NULL이 아닌 레코드만 대상으로 함
        stmt = select(Section).where(Section.essence_vector.isnot(None))

        if section_seq_list:
            stmt = stmt.where(Section.section_seq.in_(section_seq_list))

        stmt = stmt.order_by(Section.essence_vector.cosine_distance(query_vector)).limit(k)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def find_similar_sections_with_score(
            self,
            query: str,
            query_vector: List[float],
            k: int = 5,
            section_seq_list: Optional[List[int]] = None,
            semantic_weight: float = 0.7,   # 코사인 유사도
            lexical_weight: float = 0.3,    # 텍스트 유사도
        ) -> List[tuple[Section, float]]:
            
            # 기존 코사인 유사도
            semantic_score = (
                1 - Section.essence_vector.cosine_distance(query_vector)
            )

            # 키워드가 얼마나 매칭되었는지 계산
            ts_query = func.plainto_tsquery(query)

            essence_tsv = func.to_tsvector(
            'simple',
            Section.essence
            )

            raw_lexical = func.ts_rank(essence_tsv, ts_query)

            lexical_score = (
                1 - func.exp(-raw_lexical)
            )

            # 가중합
            weighted_score = (
                semantic_score * semantic_weight +
                lexical_score * lexical_weight
            )

            # 정규화
            final_score = (
                weighted_score / (semantic_weight + lexical_weight)
            ).label("score")

            stmt = (
                select(
                    Section,
                    final_score,
                )
                .where(Section.essence_vector.isnot(None))
                # .where(essence_tsv.op("@@")(ts_query)) # 테스트 위해 주석처리
            )

            if section_seq_list is not None:
                if not section_seq_list:
                    return []
                stmt = stmt.where(Section.section_seq.in_(section_seq_list))

            stmt = (
                stmt
                .order_by(final_score.desc())
                .limit(k)
            )

            result = await self.db.execute(stmt)
            return list(result.all())
            

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

    async def get_section_seq_by_keyword(self, keyword: str) -> List[dict]:
        stmt = (
            select(
                Section.section_seq,
                Section.essence,
            )
            .where(Section.essence.ilike(f"%{keyword}%"))
        )


        rows = (await self.db.execute(stmt)).mappings().all()

        return rows

    # ------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------
    async def update_section(
        self,
        section_seq: int,
        essence: str,
        essence_vector: List[float],
        tag: Optional[Any] = None,
        auto_commit: bool = True,
    ) -> Section:
        """섹션 레코드를 업데이트하고 커밋."""
        record = await self.get_section_by_id(section_seq)
        if not record:
            raise ValueError(f"Section {section_seq} not found")
        record.essence = essence
        record.essence_vector = np.array(essence_vector)
        if tag is not None:
            record.tag = tag
        self.db.add(record)
        if auto_commit:
            await self.db.commit()
            await self.db.refresh(record)
        else:
            await self.db.flush()
        return record

    # ------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------

    # ------------------------------------------------------------
    # ETC
    # ------------------------------------------------------------
