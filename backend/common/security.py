from datetime import datetime, timedelta
from typing import Optional
from common.core.crypto import CryptoService

def verify_password(plain_password, hashed_password):
    return CryptoService.verify_password_argon2(plain_password, hashed_password)

def get_password_hash(password):
    return CryptoService.encrypt_password_argon2(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return CryptoService.sign_jwt(to_encode)
