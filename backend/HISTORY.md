# Implementation Status Summary
Last Updated: 2026-01-20
Agent: Antigravity

> 가상환경은 anaconda
> **모든 암복호화는 `crypto.py`에서 관리해야 합니다.**

## 1. Authentication Infrastructure
**Status**: Completed
**Component**: `backend/common/security.py`, `backend/api_server/app/api/users.py`, `backend/api_server/app/api/auth.py`

- **Mechanism**: JWT (JSON Web Tokens) with `python-jose`.
- **Flow**:
  1. **User Sign Up**: `POST /api/v1/users` (Public). Hashes password using Argon2.
  2. **Login**: `POST /api/v1/auth/login` (Public). Accepts `OAuth2PasswordRequestForm` (Swagger UI compatible), validates Argon2 hash, returns JWT.
  3. **Router Protection**: Global `Depends(get_current_user)` applied to `/api/v1`.

## 2. Cryptographic Strategy (Hybrid)
**Status**: Completed & Centralized
**Component**: `backend/common/core/crypto.py` (`class CryptoService`)

- **Design**: All encryption logic is encapsulated in `CryptoService`.
- **Methods**:
  - **Passwords** (Argon2):
    - `encrypt_password_argon2(password)`
    - `verify_password_argon2(plain, hashed)`
  - **Blind Indexing** (HMAC-SHA256):
    - `encrypt_data_hmac(text)` (Uses `AES_SECRET_KEY` from settings)
    - Used for checking PII existence deterministically.
  - **Data Encryption** (AES-256-CBC):
    - `encrypt_data_aes(text, secret_key)`
    - `decrypt_data_aes(encrypted_text, secret_key)`
    - Requires explicit key injection (decoupled from settings) for reversible PII storage.

## 3. Privacy & Tokenization
**Status**: Completed (Routes Removed)
**Component**: `backend/api_server/app/services/document_adaption.py`

- **Workflow**:
  1. **Detection**: Loads regex patterns from `PRIVACY_PATTERNS_JSON` in `.env` (Source changed from DB to Config).
  2. **Indexing**: Uses `encrypt_data_hmac` to check against `SecureToken` table for existing entities.
  3. **Tokenization**: 
     - If new: Encrypts original text (`encrypt_data_aes`), saves to `SecureToken`, generates ID like `{{PHONE_01}}`.
     - If exists: Reuses existing token ID.
  4. **Replacement**: Replaces PII in text with token ID.
- **Note**: Privacy management APIs (`/api/v1/privacy`) have been removed in favor of `.env` configuration.

## 4. Configuration
- **File**: `.env`
- **Keys**:
  - `JWT_SECRET_KEY` (Renamed from SECRET_KEY): JWT signing.
  - `AES_SECRET_KEY`: Used for HMAC generation and passed to AES methods.
  - `PRIVACY_PATTERNS_JSON`: JSON list of regex patterns (e.g., `[{"name": "EMAIL", "pattern": "..."}]`).

## 5. Refresh Token Strategy (New)
**Status**: Implementation Started
- **Concept**: Access tokens are short-lived. Refresh tokens are long-lived and stored in DB (hashed).
- **Flow**:
  - Login returns  ccess_token + 
efresh_token.
  - 
efresh_token is opaque string, hashed with encrypt_data_hmac before DB insert.
  - POST /refresh validates hash against DB, checks expiry, returns new Access Token.
  - POST /logout removes Refresh Token from DB.
- **Components**: RefreshTokenRepository, UserService updates,  pi/auth.py endpoints.

## 6. Configuration Refactoring (Loose Definition + Strict Validation)
**Status**: Completed
- **Problem**: Shared config.py forced both servers to have all env vars, causing crashes if irrelevant keys were missing.
- **Solution**: config.py fields made Optional. Specific servers validate their required keys at startup (main.py check for API Server).

## 7. Refactoring: Naming Standardization & Clarity
**Status**: Completed
- **Changes**:
  - `user_nm` ➡ `display_name`: To clarify its role as a visible name (not a login ID).
  - `login_id` ➡ `username`: To align with OAuth2 standards.
  - `login_pwd` ➡ `password`: To align with common naming conventions.
- **Benefit**: OAuth2 fields (`username`, `password`) now directly map to DB columns without translation logic, and `display_name` is unambiguous.

## 8. 개발: 주석 및 리포지토리 리팩토링
**상태**: 완료 (2026-01-20)
**작업자**: Antigravity
- **주석 (Docstrings)**:
    - `SecureTokenRepository`, `ModelLogsRepository` 및 모든 `models.py` 클래스에 음슴체(명사형 종결) 한글 주석 적용.
- **모델 로그 저장소 (ModelLogsRepository)**:
    - 중복된 `get_by_task_id` 메서드 해결.
    - `str` 및 `UUID` 타입을 모두 지원하도록 타입 힌트 수정.
- **지식 자산 관리 (Knowledge Asset Management)**:
    - **리팩토링**: 문서 자산 생성 로직을 통합 관리하기 위해 `KnowledgeAssetRepository` (`backend/common/repositories/knowledge_asset_repo.py`) 생성.
    - **통합**: `DocumentAdaptionService.get_merge_proposal`이 `KnowledgeAssetRepository`를 사용하여 색인(Indices), 섹션(Sections), 원본 텍스트(Original Text), 레시피(Recipes)를 단일 트랜잭션 흐름으로 처리하도록 개선.
    - **신규 저장소**: `IndexRepository`, `SectionRepository` (기능 확인), `DocRecipesRepository` (수정), `SectionRecipesRepository`, `OriginalTextsRepository` (기능 확인) 추가 및 보강.
- **공통 코드 (Common Codes)**:
    - **`MergeProposalType` 추가**: 병합 제안 상태('모두 존재', '모두 신규', '제안 필요')를 관리하기 위한 Enum 정의 (`codes.py`).
