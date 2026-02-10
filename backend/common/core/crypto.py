"""
[CryptoService 3대 암호화 원칙 가이드]

이 모듈은 시스템에서 사용하는 *단 3가지*의 암호화 기술(Primitives)을 정의하고 관리합니다.
모든 보안/인증 로직은 이 3가지 기본 원칙 위에서 동작해야 합니다.

1. Argon2 (단방향 해싱)
   - 설명: 비밀번호를 암호화하는 기술. 암호화된 값으로 원래 비밀번호를 유추할 수 없습니다.
   - 용도: 회원가입 시 비밀번호 DB 저장, 로그인 시 비밀번호 검증에 사용합니다.

2. HMAC-SHA256 (서명 및 무결성)
   - 설명: 비밀키를 사용해 데이터의 위변조를 방지하는 해싱 기술. 같은 입력값과, 같은 키(Key)이면 항상 같은 결과가 나옵니다.
   - 용도 A (인증): JWT 로그인 토큰 생성 및 검증에 사용합니다. (HS256)
   - 용도 B (검색): '010-1234-5678' 같은 중요 정보를 'a1b2...' 같은 암호문으로 바꿔서, 암호화된 상태로 검색(Blind Indexing)할 때 사용합니다.

3. AES-256-CBC (양방향 암호화)
   - 설명: 열쇠(Key)로 잠그고, 다시 그 열쇠로 열 수 있는 암호화 기술.
   - 용도: 나중에 관리자가 내용을 확인해야 하는 민감 정보를 DB에 저장할 때 사용합니다. (예: 개인정보 원문)
"""
import base64
import hashlib
import hmac
import os
from typing import Optional

from jose import jwt, JWTError
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from passlib.context import CryptContext
from common.core.config import settings

class CryptoService:
    # Argon2 알고리즘 사용 (패스워드 해싱 전용 라이브러리)
    _pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

    # =============================================================
    # 1. Argon2: 비밀번호 단방향 해싱
    # =============================================================

    @classmethod
    def encrypt_password_argon2(cls, password: str) -> str:
        """
        [비밀번호 암호화]
        - 알고리즘: Argon2
        - 사용처: 회원가입 시 비밀번호를 DB에 저장하기 전 호출
        """
        return cls._pwd_context.hash(password)

    @classmethod
    def verify_password_argon2(cls, plain_password: str, hashed_password: str) -> bool:
        """
        [비밀번호 검증]
        - 알고리즘: Argon2
        - 사용처: 로그인 시 사용자가 입력한 비밀번호가 맞는지 확인
        """
        return cls._pwd_context.verify(plain_password, hashed_password)

    # =============================================================
    # 2. HMAC-SHA256: 인증 서명 및 검색용 인덱싱
    # =============================================================
    
    @staticmethod
    def sign_jwt(payload: dict) -> str:
        """
        [JWT 토큰 생성]
        - 알고리즘: HS256 (HMAC-SHA256)
        - 설명: 사용자 정보(payload)에 서명(Sign)을 하여 로그인 토큰을 발급
        - 사용처: 로그인 성공 시 Access Token 발급
        """
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

    @staticmethod
    def decode_jwt(token: str) -> dict:
        """
        [JWT 토큰 검증]
        - 알고리즘: HS256 (HMAC-SHA256)
        - 설명: 클라이언트가 보낸 토큰이 우리 서버에서 발행한 것이 맞는지 서명을 검증
        - 사용처: API 요청 시 로그인 여부 확인 (DependencyInjection)
        """
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])

    @staticmethod
    def encrypt_data_hmac(text: str) -> str:
        """
        [Blind Indexing / 검색용 해시 생성]
        - 알고리즘: HMAC-SHA256
        - 설명: 입력값이 같으면 항상 같은 암호문이 나오는 특징을 이용
        - 사용처: DB에 암호화되어 저장된 개인정보(예: 전화번호)를 검색할 때 사용 (동일성 비교용)
        """
        if not text:
            return ""
        # 인덱싱용 키(AES_SECRET_KEY) 사용
        secret_bytes = settings.AES_SECRET_KEY.encode('utf-8')
        message_bytes = text.encode('utf-8')
        return hmac.new(secret_bytes, message_bytes, hashlib.sha256).hexdigest()

    # =============================================================
    # 3. AES-256-CBC: 양방향 데이터 암호화
    # =============================================================

    @staticmethod
    def _get_aes_key(secret_key: str) -> bytes:
        """
        [내부 유틸] AES-256 키 생성
        - 설명: 설정 파일의 문자열 키를 AES 알고리즘에 맞는 32바이트 바이너리로 변환
        """
        return hashlib.sha256(secret_key.encode('utf-8')).digest()

    @staticmethod
    def encrypt_data_aes(plain_text: str) -> str:
        """
        [데이터 암호화]
        - 알고리즘: AES-256-CBC
        - 설명: 평문을 '키'를 이용해 암호문으로 변환 (복호화 가능)
        - 사용처: 개인정보 등 민감한 데이터를 DB에 저장할 때 사용
        """
        if not plain_text:
            return ""

        # 설정된 AES_SECRET_KEY 사용
        key = CryptoService._get_aes_key(settings.AES_SECRET_KEY)
        iv = os.urandom(16) # 초기화 벡터 (매번 다른 암호문을 생성하기 위해 사용)
        
        # Padding (암호화 블록 크기에 맞게 데이터 채움)
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plain_text.encode('utf-8')) + padder.finalize()

        # Encrypt
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

        # IV와 암호문을 합쳐서 Base64 문자열로 반환
        return base64.b64encode(iv + encrypted_data).decode('utf-8')

    @staticmethod
    def decrypt_data_aes(encrypted_text: str) -> str:
        """
        [데이터 복호화]
        - 알고리즘: AES-256-CBC
        - 설명: 암호문을 '키'를 이용해 원래 평문으로 복구
        - 사용처: DB에서 꺼낸 암호화된 데이터를 원래 내용으로 확인해야 할 때 사용
        """
        if not encrypted_text:
            return ""

        try:
            # Base64 디코딩
            data = base64.b64decode(encrypted_text)
            
            # IV 추출 (앞 16바이트) 및 암호문 분리
            iv = data[:16]
            encrypted_content = data[16:]
            
            key = CryptoService._get_aes_key(settings.AES_SECRET_KEY)

            # Decrypt
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(encrypted_content) + decryptor.finalize()

            # Unpad (Padding 제거)
            unpadder = padding.PKCS7(128).unpadder()
            plain_data = unpadder.update(padded_data) + unpadder.finalize()
            
            return plain_data.decode('utf-8')
        except Exception as e:
            # 복호화 실패 시 (키가 틀리거나 데이터 손상)
            print(f"Decryption error: {e}")
            return ""

