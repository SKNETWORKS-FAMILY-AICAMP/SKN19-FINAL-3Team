from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from common.models import SecureToken

class SecureTokenRepository:
    """보안 토큰 관리"""
    def __init__(self, db: AsyncSession):
        """DB 세션 초기화"""
        self.db = db

    # ------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------
    async def create_token(self, token: SecureToken) -> SecureToken:
        """토큰 생성 및 반환"""
        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)
        return token

    # ------------------------------------------------------------
    # READ
    # ------------------------------------------------------------
    async def get_by_hash(self, data_hash: str) -> Optional[SecureToken]:
        """해시로 토큰 조회"""
        query = select(SecureToken).where(SecureToken.data_hash == data_hash)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_token_text(self, token_text: str) -> Optional[SecureToken]:
        """텍스트로 토큰 조회"""
        query = select(SecureToken).where(SecureToken.token_text == token_text)
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

