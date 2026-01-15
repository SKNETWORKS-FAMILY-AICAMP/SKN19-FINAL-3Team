"""
Repository for model_logs table (AI-사용자 상호작용 로그).
비즈니스 로직은 Service 계층에 두고, 여기서는 CRUD/조회만 담당한다.
"""

import uuid
from typing import List, Optional, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from common.models import ModelLog


class ModelLogsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        *,
        operator_seq: Optional[int],
        team_seq: Optional[int],
        task_type_code: str,
        task_id: Optional[Union[str, uuid.UUID]],
        input_data,
        ai_output=None,
        user_decision=None,
    ) -> ModelLog:
        parsed_task_id = None
        if task_id:
            try:
                parsed_task_id = task_id if isinstance(task_id, uuid.UUID) else uuid.UUID(str(task_id))
            except (ValueError, TypeError):
                parsed_task_id = None

        record = ModelLog(
            operator_seq=operator_seq,
            team_seq=team_seq,
            task_type_code=task_type_code,
            task_id=parsed_task_id,
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

    async def update_by_task_id(
        self,
        task_id: str,
        *,
        # input_data=None,
        ai_output=None,
        user_decision=None,
    ) -> Optional[ModelLog]:
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

    async def get(self, log_seq: int) -> Optional[ModelLog]:
        stmt = select(ModelLog).where(ModelLog.log_seq == log_seq)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def get_by_task_id(self, task_id: str) -> Optional[ModelLog]:
        stmt = select(ModelLog).where(ModelLog.task_id == task_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_recent(
        self,
        *,
        limit: int = 50,
        operator_seq: Optional[int] = None,
        team_seq: Optional[int] = None,
    ) -> List[ModelLog]:
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

    async def get_by_task_id(self, task_id: uuid.UUID) -> Optional[ModelLog]:
        """Task ID로 로그 조회 (최신 순)"""
        stmt = (
            select(ModelLog)
            .where(ModelLog.task_id == task_id)
            .order_by(ModelLog.log_seq.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
