from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from common.models import User



class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------
    async def create_user(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    # ------------------------------------------------------------
    # READ
    # ------------------------------------------------------------
    async def get_by_username(self, username: str) -> Optional[User]:
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_seq(self, user_seq: int) -> Optional[User]:
        query = select(User).where(User.user_seq == user_seq)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def read_all_users(self) -> list[User]:
        stmt = select(User)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    # ------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------

    # ------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------

    # ------------------------------------------------------------
    # ETC
    # ------------------------------------------------------------
