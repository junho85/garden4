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

- **Framework**: Django
- **Database**: MongoDB (pymongo)
- **Integration**: Slack API (slackclient)
- **기타**: YAML, Markdown

## 설치 및 실행

### 요구사항

- Python 3.x
- MongoDB
- Slack API Token

### 설치

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 설정

1. `attendance/config.ini` 파일 생성:
```ini
[DEFAULT]
SLACK_API_TOKEN = your_slack_api_token
CHANNEL_ID = your_channel_id
GARDENING_DAYS = 100
START_DATE = 2019-10-01

[MONGO]
DATABASE = garden4
HOST = localhost
PORT = 27017

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

### 실행

```bash
# 데이터베이스 마이그레이션
python manage.py migrate

# 개발 서버 실행
python manage.py runserver
```


### Docker를 이용한 실행
Apple Silicon Mac에서 Docker를 사용하여 실행할 수 있습니다. Docker가 설치되어 있어야 합니다.

먼저, Docker 네트워크를 생성합니다.
```bash
docker network create my-app-network
```

다음으로, 네트워크에 연결해서 MongoDB 컨테이너를 실행합니다.
```bash
docker run -d --name mymongo --network my-app-network mongo
```

MongoDB 컨테이너가 실행된 후, MongoDB에 데이터를 복원합니다. `garden` 디렉토리에 있는 데이터를 `/garden` 경로로 복원합니다.
```bash
mongorestore --host="localhost" --port="27017" --db="garden" /Users/junho85/work/garden4_move/garden
```

이제 Django 애플리케이션을 실행할 수 있습니다. 현재 디렉토리를 `/app`으로 설정하고, `requirements.txt` 파일을 사용하여 의존성을 설치한 후, Django 개발 서버를 실행합니다.
```bash
docker run -it --rm -p 8000:8000 --network my-app-network -v "$(pwd):/app" -w /app python:3.6.8 bash -c "pip install -r requirements.txt && python manage.py runserver 0.0.0.0:8000"
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