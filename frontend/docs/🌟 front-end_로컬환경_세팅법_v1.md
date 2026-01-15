# back-end 세팅법


## 1. node.js 설치
현재 환경에 Node.js가 설치되지 않았다면 아래 링크에서 설치하셔야 합니다.
현재 AJC 프로젝트는 Node.js v22.19.0을 사용하고 있습니다만, 사용자 분의 기호에 맞는 버전을 설치하셔도 됩니다.
https://nodejs.org/ko/download

```shell

# 1. 우선 frontend 폴더(디렉토리)로 이동해야 합니다.
cd frontend
```

## 2. 의존성 패키지 설치
Node.js를 설치하면 기본적으로 npm도 같이 설치되지만 만약 npm 커맨드가 존재하지 않다면 최신 Node.js로 업데이트가 필요합니다.
```shell
npm install
```

# 3. 실행법
프로젝트를 dev 모드에서 시작합니다.
```shell
npm run dev
```