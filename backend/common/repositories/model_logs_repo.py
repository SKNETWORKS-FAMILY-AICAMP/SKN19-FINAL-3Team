"""
ModelLogsRepository
AI-사용자 상호작용 로그 담당
"""

import uuid
from typing import List, Optional, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from common.models import ModelLog
from datetime import datetime, timezone

class ModelLogsRepository:
    def __init__(self, db: AsyncSession):
        """DB 세션 초기화"""
        self.db = db


    def _to_naive_utc(self, dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

    # ------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------
    async def create(
        self,
        *,
        operator_seq: Optional[int],
        team_seq: Optional[int],
        task_type_code: str,
        task_id: Optional[Union[str, uuid.UUID]],
        start_task_id: Optional[Union[str, uuid.UUID]] = None,
        input_data,
        ai_output=None,
        user_decision=None,
    ) -> ModelLog:
        """로그 생성"""
        parsed_task_id = None
        if task_id:
            try:
                parsed_task_id = task_id if isinstance(task_id, uuid.UUID) else uuid.UUID(str(task_id))
            except (ValueError, TypeError):
                parsed_task_id = None
        
        parsed_start_task_id = None
        if start_task_id:
            try:
                parsed_start_task_id = start_task_id if isinstance(start_task_id, uuid.UUID) else uuid.UUID(str(start_task_id))
            except (ValueError, TypeError):
                parsed_start_task_id = None

        record = ModelLog(
            operator_seq=operator_seq,
            team_seq=team_seq,
            task_type_code=task_type_code,
            task_id=parsed_task_id,
            start_task_id=parsed_start_task_id,
            input_data=input_data,
            ai_output=ai_output,
            user_decision=user_decision,
        )
        self.db.add(record)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise
        await self.db.refresh(record)
        return record

    # ------------------------------------------------------------
    # READ
    # ------------------------------------------------------------
    async def get(self, log_seq: int) -> Optional[ModelLog]:
        """로그 시퀀스로 단일 로그 조회"""
        stmt = select(ModelLog).where(ModelLog.log_seq == log_seq)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def list_recent(
        self,
        *,
        limit: int = 50,
        operator_seq: Optional[int] = None,
        team_seq: Optional[int] = None,
    ) -> List[ModelLog]:
        """최근 로그 목록 조회"""
        stmt = select(ModelLog)
        if operator_seq is not None:
            stmt = stmt.where(ModelLog.operator_seq == operator_seq)
        if team_seq is not None:
            stmt = stmt.where(ModelLog.team_seq == team_seq)
        stmt = stmt.order_by(ModelLog.log_seq.desc()).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_by_task(
        self,
        *,
        task_type_code: str,
        task_id: uuid.UUID,
    ) -> List[ModelLog]:
        """특정 Task의 로그 목록 조회"""
        stmt = (
            select(ModelLog)
            .where(
                ModelLog.task_type_code == task_type_code,
                ModelLog.task_id == task_id,
            )
            .order_by(ModelLog.log_seq.desc())
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_task_id(self, task_id: Union[str, uuid.UUID]) -> Optional[ModelLog]:
        """Task ID로 로그 조회 (최신 순)"""
        stmt = (
            select(ModelLog)
            .where(ModelLog.task_id == task_id)
            .order_by(ModelLog.log_seq.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()


    async def read_audit_log(self, start_date=None, end_date=None, task_type_code=None, operator_seq=None, team_seq=None):
        """감사 로그 조회 (필터 기능)"""
        stmt = select(ModelLog)

        if start_date:
            stmt = stmt.where(ModelLog.created_at >= self._to_naive_utc(start_date))

        if end_date:
            stmt = stmt.where(ModelLog.created_at <= self._to_naive_utc(end_date))

        if task_type_code:
            stmt = stmt.where(ModelLog.task_type_code == task_type_code)

        if operator_seq:
            stmt = stmt.where(ModelLog.operator_seq == operator_seq)

        if team_seq:
            stmt = stmt.where(ModelLog.team_seq == team_seq)

        result = await self.db.execute(stmt)
        return result.scalars().all()




    # ------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------
    async def update_by_task_id(
        self,
        task_id: str,
        *,
        # input_data=None,
        ai_output=None,
        user_decision=None,
    ) -> Optional[ModelLog]:
        """Task ID로 로그 업데이트"""
        record = await self.get_by_task_id(task_id)
        if not record:
            return None

        # if input_data is not None:
        #     record.input_data = input_data
        if ai_output is not None:
            record.ai_output = ai_output
        if user_decision is not None:
            record.user_decision = user_decision

        self.db.add(record)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise
        await self.db.refresh(record)
        return record

    # ------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------

    # ------------------------------------------------------------
    # ETC
    # ------------------------------------------------------------
