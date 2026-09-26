# Garden4 배포 가이드

## 1. Docker 컨테이너 실행

### 방법 1: 환경 변수 사용

```bash
# Docker Hub에서 이미지 가져오기
docker pull junho85/garden4:latest

# 컨테이너 실행
docker run -d \
  --name garden4 \
  -p 127.0.0.1:8004:8000 \
  --restart unless-stopped \
  -e DEBUG=0 \
  -e ALLOWED_HOSTS=garden4.junho85.pe.kr \
  -e DB_HOST=aws-0-ap-northeast-2.pooler.supabase.com \
  -e DB_PORT=6543 \
  -e DB_NAME=postgres \
  -e DB_USER=postgres.schejihwxwsvaduhpkbe \
  -e DB_PASSWORD=... \
  -e DB_SCHEMA=garden4 \
  -e SLACK_API_TOKEN=... \
  -e CHANNEL_ID=CNPL98TAQ \
  junho85/garden4:latest
```

### 방법 2: 설정 파일 사용 (config.ini, users.yaml)

```bash
# 설정 파일 디렉토리 생성
mkdir -p ~/garden4-config

# config.ini 파일 생성
cat > ~/garden4-config/config.ini << 'EOF'
; config.ini
[DEFAULT]
SLACK_API_TOKEN = your-slack-api-token
CHANNEL_ID = your-channel-id

START_DATE = 2019-10-01
GARDENING_DAYS = 100

[POSTGRESQL]
DATABASE = postgres
HOST = your-db-host
PORT = 6543
USER = your-db-user
PASSWORD = your-db-password
SCHEMA = garden4

[GITHUB]
USERS = user1,user2,user3
EOF

# users.yaml 파일 생성
cat > ~/garden4-config/users.yaml << 'EOF'
user1:
  slack: slack-username1
user2:
  slack: slack-username2
EOF

# 설정 파일을 마운트하여 컨테이너 실행
docker run -d \
  --name garden4 \
  -p 127.0.0.1:8004:8000 \
  --restart unless-stopped \
  -v ~/garden4-config/config.ini:/app/attendance/config.ini:ro \
  -v ~/garden4-config/users.yaml:/app/attendance/users.yaml:ro \
  -e DEBUG=0 \
  -e ALLOWED_HOSTS=garden4.junho85.pe.kr \
  junho85/garden4:latest
```

## 2. Nginx 설정

### Nginx 설정 파일 복사
```bash
# Nginx 설정 파일 복사
sudo cp nginx-server.conf /etc/nginx/sites-available/garden4

# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/garden4 /etc/nginx/sites-enabled/

# Nginx 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl reload nginx
```

## 3. SSL 인증서 설정 (Let's Encrypt)

```bash
# Certbot 설치 (Ubuntu/Debian)
sudo apt update
sudo apt install certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d garden4.junho85.pe.kr
```

## 4. 서비스 확인

```bash
# Docker 컨테이너 상태 확인
docker ps | grep garden4

# 로그 확인
docker logs garden4

# 헬스체크
curl http://localhost:8004/attendance/
```

## 5. 업데이트 방법

```bash
# 새 이미지 가져오기
docker pull junho85/garden4:latest

# 기존 컨테이너 중지 및 제거
docker stop garden4
docker rm garden4

# 새 컨테이너 실행 (위의 docker run 명령어 사용)
```

## 6. 문제 해결

### 502 Bad Gateway
- Docker 컨테이너가 실행 중인지 확인: `docker ps`
- 포트 바인딩 확인: `netstat -tlnp | grep 8004`

### 권한 문제
- SELinux 사용 시: `sudo setsebool -P httpd_can_network_connect 1`