# Garden4 Backend
정원사들 시즌4 출석부입니다.
GitHub 활동 기반 출석 체크 시스템의 백엔드 애플리케이션입니다.

## 개요

Garden4는 GitHub 커밋 활동을 Slack을 통해 수집하고 출석 현황을 관리하는 Django 기반 백엔드 시스템입니다. 사용자들의 일일 커밋 활동을 추적하여 출석을 자동으로 체크합니다.

## 주요 기능

- GitHub 커밋 활동을 Slack 메시지로 수집
- 사용자별 출석 현황 관리
- 미출석자 알림 기능
- 출석 통계 CSV 생성
- RESTful API 제공

## 기술 스택

- **Framework**: Django 4.2.11
- **Database**: PostgreSQL (Supabase)
- **Integration**: Slack API (slack-sdk)
- **기타**: YAML, Markdown
- **Deployment**: Docker, Docker Compose

## 설치 및 실행

### 요구사항

- Python 3.11+
- Docker (권장)
- Slack API Token

## Docker 실행 (권장)

### 로컬 개발 환경

1. **Docker-Garden 저장소에서 실행** (권장):
```bash
cd /Users/junho85/WebstormProjects/docker-garden

# garden4 서비스만 실행
docker-compose up web-garden4
```
- 포트: http://localhost:8004
- 로컬 소스 코드를 자동으로 빌드
- 코드 변경 시 자동 반영

2. **프로젝트 디렉토리에서 직접 실행**:
```bash
cd /path/to/garden4-backend

# Docker 이미지 빌드 및 실행
docker build -t garden4-backend .
docker run -p 8000:8000 garden4-backend
```

### 배포용 이미지 빌드

멀티 플랫폼 지원 (Apple Silicon + AMD64):

```bash
cd /path/to/garden4-backend

# 멀티 플랫폼 빌드 및 Docker Hub 푸시
./build-and-push.sh
```

또는 수동으로:
```bash
# buildx 빌더 생성
docker buildx create --name multiplatform --use

# 멀티 플랫폼 빌드 및 푸시
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag junho85/garden4:latest \
  --tag junho85/garden4:$(date +%Y%m%d_%H%M%S) \
  --push \
  .
```

## 로컬 개발 환경 (Python)

### 설정

1. `attendance/config.ini` 파일 생성:
```ini
[DEFAULT]
SLACK_API_TOKEN = your_slack_api_token
CHANNEL_ID = your_channel_id
GARDENING_DAYS = 100
START_DATE = 2019-10-01

[POSTGRESQL]
DATABASE = postgres
HOST = your_supabase_host
PORT = 6543
USER = your_user
PASSWORD = your_password
SCHEMA = garden4

[GITHUB]
USERS = user1,user2,user3
```

2. `attendance/users.yaml` 파일 생성:
```yaml
user1:
  slack: slack_username1
user2:
  slack: slack_username2
```

### 설치 및 실행

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 마이그레이션
python manage.py migrate

# 개발 서버 실행
python manage.py runserver
```

## 주요 명령어

### Slack 메시지 수집
```bash
python attendance/cli_collect.py
```

### 미출석자 알림
```bash
python attendance/cli_noti_no_show.py
```

## API 엔드포인트

- `/attendance/` - 출석 관련 API

## 프로젝트 구조

```
garden4-backend/
├── attendance/          # 출석 관리 앱
│   ├── garden.py       # 핵심 로직
│   ├── views.py        # API 뷰
│   ├── urls.py         # URL 라우팅
│   └── cli_*.py        # CLI 스크립트
├── mysite/             # Django 프로젝트 설정
├── manage.py           # Django 관리 스크립트
└── requirements.txt    # 의존성 목록
```