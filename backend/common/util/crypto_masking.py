import re
import json
import base64
import hashlib
import os
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from common.core.crypto import CryptoService as crypto_tool
from common.repositories.secure_token_repo import SecureTokenRepository
from common.models import SecureToken


class InfoMask :
    def __init__(self, secure_repo, pattern_repo) :
        """
        Args:
            secure_repo: SecureTokenRepository for token storage
            pattern_repo: PatternRepository for pattern management
        """
        self.secure_repo = secure_repo
        self.pattern_repo = pattern_repo

    async def load_patterns(self) -> dict:
        """DB에서 활성화된 패턴만 로드"""
        patterns = await self.pattern_repo.read_all_patterns()
        return {
            p.pattern_name: p.regex_pattern 
            for p in patterns 
            if p.is_active
        }

    async def add_pattern(self, pattern_name: str, regex_pattern: str) -> None:
        """
        패턴을 DB에 추가
        Args:
            pattern_name: 패턴 이름 (예: RRN_PATTERN)
            regex_pattern: 정규식 패턴
        """
        from common.models import Pattern
        new_pattern = Pattern(
            pattern_name=pattern_name,
            regex_pattern=regex_pattern,
            is_active=True
        )
        await self.pattern_repo.create_pattern(new_pattern)

    async def get_pattern(self) -> dict:
        """현재 활성화된 모든 패턴 반환"""
        return await self.load_patterns()

    # 탐지된 문자열을 단방향 암호화한 후 DB에서 검색하고, 결과를 반환
    async def _search_with_text(self, text: str) -> str :
        hash = crypto_tool.encrypt_data_hmac(text)


        mask = await self.secure_repo.get_by_hash(hash)

        if mask :
            return mask.token_text
        else :
            return None

    # 문자열을 탐지 후 마스킹
    async def _mask_with_pattern(
        self,
        text: str,
        pattern: str,
        pattern_name: str
    ):
        mask_to_original = {}      # 새로 생성된 것만
        original_to_mask = {}      # 치환용 (전체)

        originals = set(m.group(0) for m in re.finditer(pattern, text))
        if not originals:
            return text, {}

        for original in originals:
            existing_key = await self._search_with_text(original)

            if existing_key:
                masked_key = existing_key
                masked = f"{{{{{masked_key}}}}}"

                original_to_mask[original] = masked

            else:
                masked_key = f"{pattern_name}_{uuid.uuid4().hex[:8]}"
                masked = f"{{{{{masked_key}}}}}"

                original_to_mask[original] = masked
                mask_to_original[masked_key] = original

        def replacer(match: re.Match) -> str:
            return original_to_mask[match.group(0)]

        masked_text = re.sub(pattern, replacer, text)

        return masked_text, mask_to_original

    # 식별된 패턴을 암호화
    def _encrypt_data_dict(self, patterns : dict) -> dict:
        for key, value in patterns.items() :
            patterns[key] = { "original" : value,
                              "encrypt" : crypto_tool.encrypt_data_aes(value)}

        return patterns
    
    # 데이터를 기반으로 텍스트를 복호화하는 전체 로직
    async def decrypt_text(self, text: str) -> str:
        MASK_PATTERN = r"\{\{[A-Z_]+_[a-f0-9]{8}\}\}"

        tokens = set(re.findall(MASK_PATTERN, text))

        if not tokens:
            return text

        for full_token in tokens:
            token_text = full_token[2:-2]
            encrypted_text = await self.secure_repo.get_by_token_text(token_text)
            if not encrypted_text:
                continue

            decrypted = crypto_tool.decrypt_data_aes(encrypted_text.ciphertext)

            text = text.replace(full_token, decrypted)

        return text

    # 텍스트를 암호화하는 전체 로직
    async def encrypt_text(self, text: str) -> str :
        # DB에서 패턴 로드 (매번 최신 상태 반영)
        patterns = await self.load_patterns()
        
        masked_text = text
        masked_dict = {}
        for pattern_name, pattern in patterns.items() :
            masked_text, dict = await self._mask_with_pattern(masked_text, pattern, pattern_name)
            masked_dict[pattern_name] = self._encrypt_data_dict(dict)

        for type, data in masked_dict.items() :
            for key, value in data.items() :
                data_hash = crypto_tool.encrypt_data_hmac(value['original'])
                input_token = {
                    "token_text" : key,
                    "data_type" : type,
                    "ciphertext" : value['encrypt'],
                    "data_hash" : data_hash
                }
                class_token = SecureToken(**input_token)
                token = await self.secure_repo.create_token(class_token)

        return masked_text

