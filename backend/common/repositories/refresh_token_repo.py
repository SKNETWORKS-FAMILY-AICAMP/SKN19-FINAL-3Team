from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from common.models import RefreshToken

class RefreshTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------
    async def create(self, refresh_token: RefreshToken) -> RefreshToken:
        self.db.add(refresh_token)
        await self.db.commit()
        await self.db.refresh(refresh_token)
        return refresh_token

    # ------------------------------------------------------------
    # READ
    # ------------------------------------------------------------
    async def get_by_token_value(self, token_value: str) -> Optional[RefreshToken]:
        # token_value stored is hashed
        query = select(RefreshToken).where(RefreshToken.token_value == token_value)
        result = await self.db.execute(query)
        return result.scalars().first()

    # ------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------

    # ------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------
    async def delete_by_token_value(self, token_value: str) -> None:
        query = delete(RefreshToken).where(RefreshToken.token_value == token_value)
        await self.db.execute(query)
        await self.db.commit()

    async def delete_expired_tokens(self) -> None:
        # Maintenance method, logic to be implemented if needed
        pass

    # ------------------------------------------------------------
    # ETC
    # ------------------------------------------------------------
