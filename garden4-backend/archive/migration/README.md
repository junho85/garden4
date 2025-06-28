# MongoDB to Supabase Migration Guide

## Overview
이 가이드는 Garden4 프로젝트의 MongoDB 데이터베이스를 Supabase (PostgreSQL)로 마이그레이션하는 방법을 설명합니다.

## 마이그레이션 전략

### 1. 스키마 설계
- Supabase에서 `garden4` 스키마를 사용하여 다른 프로젝트와 분리
- `slack_messages` 테이블에 JSONB 타입을 사용하여 MongoDB의 유연한 구조 유지
- 인덱스를 통해 쿼리 성능 최적화

### 2. 데이터 구조
```sql
-- Supabase 테이블 구조
CREATE TABLE garden4.slack_messages (
    id UUID PRIMARY KEY,
    ts VARCHAR(20) UNIQUE NOT NULL,  -- Slack timestamp
    ts_for_db TIMESTAMP NOT NULL,     -- 쿼리용 timestamp
    bot_id VARCHAR(20),
    type VARCHAR(20),
    text TEXT,
    user VARCHAR(20),
    team VARCHAR(20),
    bot_profile JSONB,               -- JSON 데이터
    attachments JSONB,               -- GitHub 커밋 정보 배열
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 마이그레이션 단계

### 1. Supabase 프로젝트 설정

1. Supabase 대시보드에서 SQL 에디터 열기
2. `supabase_schema.sql` 파일의 내용 실행
3. Service Role Key 확인 (Settings > API)

### 2. 환경 변수 설정

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-role-key"
export SUPABASE_ANON_KEY="your-anon-key"
```

### 3. 필요한 패키지 설치

```bash
pip install supabase pymongo bson
```

### 4. 데이터 마이그레이션 실행

```bash
# BSON 파일에서 직접 마이그레이션
python migration/mongodb_to_supabase.py

# 또는 실행 중인 MongoDB에서 마이그레이션
python migration/migrate_from_running_mongodb.py
```

### 5. 코드 업데이트

#### 기존 MongoDB 코드:
```python
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['garden']
collection = db['slack_messages']

# 쿼리 예제
docs = collection.find({"ts_for_db": {"$gte": start_date}})
```

#### Supabase 어댑터 사용:
```python
from attendance.supabase_adapter import SupabaseAdapter

db = SupabaseAdapter(supabase_url, supabase_key, schema='garden4')

# 동일한 쿼리 인터페이스
docs = db.find({"ts_for_db": {"$gte": start_date}})
```

## 주요 변경사항

### 1. 연결 설정
- MongoDB URI 대신 Supabase URL과 API 키 사용
- 스키마를 통한 프로젝트 분리 (`garden4`)

### 2. 쿼리 변환
- MongoDB 스타일 쿼리를 PostgreSQL로 자동 변환
- JSONB 필드에 대한 쿼리 지원

### 3. 성능 최적화
- 적절한 인덱스 생성
- View를 통한 쿼리 간소화
- RLS (Row Level Security) 정책 적용

## 테스트 방법

### 1. 데이터 무결성 확인
```python
# MongoDB 데이터 수
mongo_count = mongodb_collection.count_documents({})

# Supabase 데이터 수
supabase_count = supabase_db.count_documents({})

assert mongo_count == supabase_count
```

### 2. 쿼리 결과 비교
```python
# 특정 날짜 범위 쿼리
from datetime import datetime, timedelta

start_date = datetime.now() - timedelta(days=7)
end_date = datetime.now()

# MongoDB 결과
mongo_results = list(mongodb_collection.find({
    "ts_for_db": {"$gte": start_date, "$lt": end_date}
}).sort("ts", 1))

# Supabase 결과
supabase_results = supabase_db.find({
    "ts_for_db": {"$gte": start_date, "$lt": end_date}
}, sort=[("ts", 1)])

# 결과 비교
assert len(mongo_results) == len(supabase_results)
```

## 롤백 계획

만약 문제가 발생하면:

1. 기존 MongoDB 연결로 되돌리기
2. 환경 변수를 MongoDB 설정으로 변경
3. 코드에서 adapter import를 pymongo로 변경

## 모니터링

- Supabase 대시보드에서 쿼리 성능 모니터링
- 에러 로그 확인
- API 사용량 모니터링

## 문제 해결

### 1. 중복 키 오류
- `ts` 필드가 unique이므로 중복 데이터 확인
- 마이그레이션 스크립트의 개별 삽입 로직 활용

### 2. JSONB 쿼리 오류
- PostgreSQL JSONB 쿼리 문법 확인
- 어댑터의 쿼리 변환 로직 검토

### 3. 성능 이슈
- 인덱스 생성 확인
- 쿼리 플랜 분석 (EXPLAIN ANALYZE)
- 배치 크기 조정

## 참고 자료

- [Supabase 문서](https://supabase.com/docs)
- [PostgreSQL JSONB 가이드](https://www.postgresql.org/docs/current/datatype-json.html)
- [Supabase Python 클라이언트](https://github.com/supabase-community/supabase-py)