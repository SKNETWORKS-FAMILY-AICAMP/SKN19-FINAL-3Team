# 🛠️ 백엔드 개발 환경 및 실행 가이드

팀원들이 각자의 PC에서 원활하게 개발 및 디버깅할 수 있도록 전체 환경을 설정하는 방법입니다.

---

## 0. 초기 설정 (.env 파일 생성)
**Why?**: `docker-compose`는 실행 시 모든 서비스의 설정 파일(`.env`) 존재 여부를 확인합니다. Redis만 실행하더라도 다른 서버들의 `.env` 파일이 없으면 에러(`env file not found`)가 발생합니다.

아래 내용을 복사하여 각 경로에 파일을 생성해주세요.

**A. `backend/api_server/.env` 생성**
```env

```

**B. `backend/ai_server/.env` 생성**
(위 내용과 동일합니다. 파일만 따로 만들어주세요.)

---

## 1. Redis 실행 (필수)
**Why?**: AI Server와 API Server가 통신하기 위한 메시지 큐(Message Queue) 역할을 합니다. 로컬 개발 시에도 Redis가 켜져 있어야 서버가 에러 없이 실행됩니다.

(Docker Desktop이 설치되어 있어야 합니다.)

터미널(PowerShell)을 열고 **`docker-compose.yml` 파일이 있는 `backend` 폴더**로 이동해서 실행해야 합니다.

```shell
# 1. backend 폴더로 이동 (프로젝트 루트 기준)
cd backend

# 2. Redis 컨테이너만 백그라운드로 실행
docker-compose up -d redis

# 3. 실행 확인
docker ps
# (ajc_redis 컨테이너가 보여야 함)
```
> **💡 Docker Desktop 팁**: 
> `docker-compose`로 실행하면 **`backend`라는 그룹(폴더)** 안에 컨테이너가 묶입니다. 
> 포트(`6379`)가 안 보인다면, 목록에서 `backend` 그룹 왼쪽의 **화살표(>)를 눌러 펼쳐보세요.**
> **참고**: 만약 `docker-compose` 대신 순수 Docker 명령어로 띄우고 싶다면:
> `docker run -d --name ajc_redis -p 6379:6379 redis:alpine`

---

## 2. Anaconda 가상환경 생성 (각 서버별 분리)
**Why?**: API 서버와 AI 서버의 의존성을 분리하여 충돌을 막고, 필요한 것만 설치하여 가볍고 쾌적한 환경을 유지하기 위함.

### A. API 서버용 환경 (`ajc_api`)
터미널에서 아래 명령어를 순서대로 실행하세요.

```shell
# 1. 환경 생성 (Python 3.11)
conda create -n ajc_api python=3.11 -y

# 2. 활성화
conda activate ajc_api

# 3. 의존성 설치 (가벼움 - FastAPI 등)
cd backend/api_server
pip install -r requirements.txt
```

### B. AI 서버용 환경 (`ajc_ai`)
AI 관련 무거운 라이브러리는 여기에만 설치합니다.

```shell
# 1. 환경 생성 (Python 3.11)
conda create -n ajc_ai python=3.11 -y

# 2. 활성화
conda activate ajc_ai

# 3. 의존성 설치 (무거움 - PyTorch, LlamaIndex 등)
cd backend/ai_server
pip install -r requirements.txt
```

---

## 3. VS Code 파이썬 경로 인식 설정
**Why?**: VS Code가 `common` 같은 공통 폴더의 코드를 인식하게 하여, **빨간 줄(Import Error)을 없애고 자동완성** 기능을 쓰기 위함.

프로젝트 최상위 폴더의 `.vscode/settings.json` 파일을 열고(없으면 생성) 아래 내용을 넣으세요.

```json
{
    "python-envs.pythonProjects": [],
    "python.analysis.extraPaths": [
        "./backend",
        "./backend/common",
        "./backend/api_server",
        "./backend/ai_server"
    ]
}
```

---

## 4. 디버거 실행 설정 (VS Code F5)
**Why?**: 매번 터미널에 긴 명령어를 치지 않고, **버튼 클릭(F5) 한 번으로 서버를 실행**하고 **중단점(Breakpoint)**을 찍어 코드를 분석하기 위함.

`.vscode/launch.json` 파일을 열고 아래 내용을 붙여넣으세요.

> **⚠️ 필독**: `"python"` 항목의 경로는 **반드시 본인의 PC conda 경로**에 맞게 수정해야 합니다! 
> (터미널에서 `conda env list` 입력 시 확인 가능)

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "API Server",
            "type": "debugpy",
            "request": "launch",
            "python": "C:/Users/{사용자명}/anaconda3/envs/ajc_api/python.exe",
            "module": "uvicorn",
            "args": [
                "app.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--reload"
            ],
            "cwd": "${workspaceFolder}/backend/api_server",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/backend;${workspaceFolder}/backend/api_server",
                "PYTHONIOENCODING": "utf-8"
            },
            "envFile": "${workspaceFolder}/backend/api_server/.env",
            "console": "integratedTerminal"
        },
        {
            "name": "AI Server",
            "type": "debugpy",
            "request": "launch",
            "python": "C:/Users/{사용자명}/anaconda3/envs/ajc_ai/python.exe",
            "module": "app.worker",
            "cwd": "${workspaceFolder}/backend/ai_server",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/backend;${workspaceFolder}/backend/ai_server",
                "PYTHONIOENCODING": "utf-8"
            },
            "envFile": "${workspaceFolder}/backend/ai_server/.env",
            "console": "integratedTerminal"
        }
    ],
    "compounds": [
        {
            "name": "API + AI", // 두 서버 동시 실행 프로필
            "configurations": [
                "API Server",
                "AI Server"
            ],
            "stopAll": true // 하나를 끄면 나머지도 같이 종료
        }
    ]
}
```

---

## 5. 실행 방법 (VS Code 사용)
**Why?**: API 서버와 AI 서버가 연동되어 작동하므로, **두 서버를 동시에 켜서 통합 테스트**를 하기 위함.

1. **Redis 실행 확인**: `docker ps`로 redis가 켜져 있는지 먼저 확인.
2. VS Code 좌측 메뉴바에서 **'Run and Debug'** 아이콘(벌레와 실행 아이콘) 클릭. (단축키: `Ctrl+Shift+D`)
3. 상단 드롭다운 목록에서 **`API + AI`** 선택.
4. **초록색 재생 버튼(▶)** 클릭.
5. 하단 터미널 창이 갈라지며 **API Server**와 **AI Server**가 동시에 실행되는지 확인.

---

## 6. 터미널(Shell)에서 직접 실행 방법
VS Code 디버거를 사용하지 않고 파워쉘(PowerShell)에서 직접 실행해야 할 경우 아래 명령어를 사용하세요.

### A. API Server 실행
```powershell
$env:PYTHONPATH="c:\SKN_19\poli-cheetah\backend;c:\SKN_19\poli-cheetah\backend\api_server"
$env:PYTHONIOENCODING="utf-8"
cd c:\SKN_19\poli-cheetah\backend\api_server
& "C:/Users/Playdata/anaconda3/envs/ajc_api/python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --env-file .env
```

### B. AI Worker 실행
```powershell
$env:PYTHONPATH="c:\SKN_19\poli-cheetah\backend;c:\SKN_19\poli-cheetah\backend\ai_server"
$env:PYTHONIOENCODING="utf-8"
cd c:\SKN_19\poli-cheetah\backend\ai_server
& "C:/Users/Playdata/anaconda3/envs/ajc_ai/python.exe" -m app.worker
```

---

## 7. 🐳 [배포 매뉴얼] 서버별 도커 컨테이너 실행 가이드

본 문서는 팀원들이 **AI 서버**와 **API 서버**를 각각의 역할에 맞춰 독립적으로 배포하고 실행하기 위한 매뉴얼입니다.

### 📋 개요 (Architecture)
우리 서비스는 두 개의 독립적인 도커 그룹으로 나뉩니다.

1.  **AI Server Group** (연산 담당)
    *   `ajc_worker`: AI 모델을 로드하고 작업을 수행하는 워커
    *   `ajc_redis`: 작업 메시지를 중개하는 큐 (**AI Server에 포함되어 배포됨**)

2.  **API Server Group** (Interface 담당)
    *   `ajc_api`: 클라이언트 요청을 받는 웹 서버

### 🚀 A. AI Server (+Redis) 배포 및 실행
AI 기능을 담당하는 서버에서 실행합니다. Redis가 함께 실행됩니다.

**실행 명령어** (`backend` 폴더에서 실행)
```bash
# AI Worker와 Redis만 실행 (빌드 포함)
docker-compose up -d --build backend-ai redis

# 로그 확인
docker-compose logs -f backend-ai
```

### 🌐 B. API Server 배포 및 실행
웹 요청을 처리하는 서버에서 실행합니다.
> **주의**: API 서버는 Redis에 연결해야 하므로, **AI Server(Redis)가 먼저 켜져 있어야 합니다.** (같은 네트워크 내)

**실행 명령어** (`backend` 폴더에서 실행)
```bash
# API Server만 실행 (빌드 포함)
docker-compose up -d --build backend-api

# 로그 확인
docker-compose logs -f backend-api
```

### 🛑 C. 서비스 종료
```bash
# 전체 종료
docker-compose down

# 특정 서버만 종료
docker-compose stop backend-worker
docker-compose stop backend-api
```

### 🛠 (참고) 환경 설정 파일
| 파일 위치 | 역할 | 주요 확인 변수 |
| :--- | :--- | :--- |
| `ai_server/.env` | AI Worker 설정 | `REDIS_HOST`, `DB_HOST` |
| `api_server/.env` | API Server 설정 | `REDIS_HOST`, `DB_HOST` |

