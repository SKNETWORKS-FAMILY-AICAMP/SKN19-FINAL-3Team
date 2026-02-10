from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from common.models import Team

class TeamRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------
    async def create_team(self, team: Team) -> Team:
        self.db.add(team)
        await self.db.commit()
        await self.db.refresh(team)
        return team

    # ------------------------------------------------------------
    # READ
    # ------------------------------------------------------------
    async def get_by_name(self, team_name: str) -> Optional[Team]:
        query = select(Team).where(Team.team_name == team_name)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_seq(self, team_seq: int) -> Optional[Team]:
        query = select(Team).where(Team.team_seq == team_seq)
        result = await self.db.execute(query)
        return result.scalars().first()

    # ------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------

    # ------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------

    # ------------------------------------------------------------
    # ETC
    # ------------------------------------------------------------
    