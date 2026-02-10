from typing import Optional
import secrets
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from common.models import User, RefreshToken
from common.schemas import UserCreate, UserLogin
from common.repositories.user_repo import UserRepository
from common.repositories.refresh_token_repo import RefreshTokenRepository
from common.security import get_password_hash, verify_password, create_access_token
from common.core.config import settings
from common.core.crypto import CryptoService
from fastapi import HTTPException, status

class UserService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)
        self.refresh_token_repo = RefreshTokenRepository(db)

    async def create_user(self, user_in: UserCreate) -> User:
        # Check if user exists
        existing_user = await self.user_repo.get_by_username(user_in.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
        
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            display_name=user_in.display_name,
            username=user_in.username,
            password=hashed_password,
            status_code="ACTIVE"
        )
        return await self.user_repo.create_user(db_user)

    async def authenticate_user(self, user_in: UserLogin):
        user = await self.user_repo.get_by_username(user_in.username)
        if not user:
            return None
        if not verify_password(user_in.password, user.password):
            return None
        return user

    async def create_tokens(self, user: User, device_info: str = None):
        # 1. Access Token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        # 2. Refresh Token
        # Generate random string
        raw_refresh_token = secrets.token_urlsafe(32)
        # Hash for storage (using HMAC as blind index style per crypto policy)
        hashed_refresh_token = CryptoService.encrypt_data_hmac(raw_refresh_token)
        
        refresh_expires = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        db_refresh_token = RefreshToken(
            user_seq=user.user_seq,
            token_value=hashed_refresh_token,
            expires_at=refresh_expires,
            device_info=device_info
        )
        await self.refresh_token_repo.create(db_refresh_token)

        return {
            "access_token": access_token, 
            "refresh_token": raw_refresh_token, 
            "token_type": "bearer"
        }

    async def refresh_access_token(self, start_refresh_token: str):
        # 1. Verify existence in DB
        hashed_token = CryptoService.encrypt_data_hmac(start_refresh_token)
        stored_token = await self.refresh_token_repo.get_by_token_value(hashed_token)
        
        if not stored_token:
             # Invalid token
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 2. Check expiration
        if stored_token.expires_at < datetime.utcnow():
            # Delete expired token
            await self.refresh_token_repo.delete_by_token_value(hashed_token)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 3. Get User
        # NOTE: RefreshToken model has user_seq, but we need username for access token sub
        # We need a method to get user by seq or fetch eager loaded
        # For now, let's fetch user by seq
        user = await self.user_repo.get_by_seq(stored_token.user_seq)
        if not user:
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 4. Issue new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "refresh_token": start_refresh_token, # Return same refresh token
            "token_type": "bearer"
        }

    async def logout(self, refresh_token: str):
        hashed_token = CryptoService.encrypt_data_hmac(refresh_token)
        await self.refresh_token_repo.delete_by_token_value(hashed_token)

    # Legacy support (removed or kept for compatibility if needed, but updated to use new flow if called)
    # The previous `create_token` was synchronous and didn't save to DB. 
    # We should deprecate it or update it. 
    # Since `login` endpoint calls this, we should replace `login` endpoint logic.

