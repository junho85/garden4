# JSON을 INSERT SQL로 변환하고 마이그레이션하는 방법

## 개요
MongoDB에서 내보낸 JSON 데이터를 PostgreSQL (Supabase)의 INSERT SQL 문으로 변환하고 마이그레이션하는 전체 과정을 설명합니다.

## 파일 구조
```
migration/
├── json_to_sql.py         # JSON → SQL 변환 스크립트
├── json_to_supabase.py    # JSON → Supabase 직접 삽입
└── slack_messages_import.sql  # 생성된 SQL 파일
```

## 방법 1: JSON을 SQL 파일로 변환 후 수동 실행

### 1.1 스크립트 실행
```bash
cd migration
python json_to_sql.py
```

### 1.2 변환 과정
`json_to_sql.py`는 다음 단계를 수행합니다:

1. **JSON 파일 읽기**: 각 라인을 개별 JSON 문서로 파싱
2. **데이터 변환**:
   - `_id` 필드 제거 (MongoDB ObjectId)
   - `ts_for_db.$date.$numberLong` → ISO timestamp 변환
   - `$numberInt` 타입 → 정수 변환
   - JSON 객체/배열 → 이스케이프된 JSON 문자열
3. **SQL 생성**:
   - 100개 문서씩 배치로 그룹화
   - `ON CONFLICT (ts) DO NOTHING` 로 중복 방지

### 1.3 생성되는 SQL 구조
```sql
SET search_path TO garden4;

-- Batch 1/10 (Documents 1-100)
INSERT INTO slack_messages (ts, ts_for_db, bot_id, type, text, "user", team, bot_profile, attachments)
VALUES
  ('1234567890.123456', '2024-06-22T10:30:00', 'B01ABC123', 'message', 'Hello World', 'U01XYZ789', 'T01DEF456', '{"name": "bot"}', '[{"id": 1}]'),
  ('1234567890.234567', '2024-06-22T10:31:00', NULL, 'message', 'Another message', 'U01ABC123', 'T01DEF456', NULL, NULL)
ON CONFLICT (ts) DO NOTHING;
```

### 1.4 SQL 실행
1. Supabase 대시보드 → SQL Editor
2. 생성된 `slack_messages_import.sql` 내용 복사/붙여넣기
3. 실행

## 방법 2: Python으로 Supabase에 직접 삽입

### 2.1 환경 설정
```bash
# 패키지 설치
pip install supabase python-dotenv

# 환경 변수 설정 (.env 파일)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

### 2.2 스크립트 실행
```bash
python json_to_supabase.py
```

### 2.3 변환 과정
`json_to_supabase.py`의 주요 기능:

1. **문서 변환** (`transform_document` 함수):
   ```python
   def transform_document(doc):
       # MongoDB _id 제거
       if '_id' in doc and '$oid' in doc['_id']:
           del doc['_id']
       
       # 날짜 변환
       if 'ts_for_db' in doc and '$date' in doc['ts_for_db']:
           timestamp_ms = int(doc['ts_for_db']['$date']['$numberLong'])
           doc['ts_for_db'] = datetime.fromtimestamp(timestamp_ms / 1000).isoformat()
       
       # JSON 필드 문자열화
       if 'bot_profile' in doc and isinstance(doc['bot_profile'], dict):
           doc['bot_profile'] = json.dumps(doc['bot_profile'])
       
       return doc
   ```

2. **배치 삽입**:
   - 50개 문서씩 배치로 처리
   - 배치 실패 시 개별 삽입으로 fallback
   - 중복 키 오류 자동 처리

## 데이터 변환 규칙

### MongoDB → PostgreSQL 타입 매핑
| MongoDB 타입 | PostgreSQL 타입 | 변환 방법 |
|-------------|----------------|----------|
| `ObjectId` | 제거 | `_id` 필드 삭제 |
| `ISODate` | `TIMESTAMP` | ISO 8601 문자열로 변환 |
| `NumberInt` | `INTEGER` | 정수로 변환 |
| `Object` | `JSONB` | JSON 문자열로 직렬화 |
| `Array` | `JSONB` | JSON 문자열로 직렬화 |

### 특수 필드 처리
1. **ts_for_db**: `$date.$numberLong` → ISO timestamp
2. **bot_profile**: 중첩 객체의 `$numberInt` 처리
3. **attachments**: 배열 내 객체의 `$numberInt` 처리
4. **user**: PostgreSQL 예약어이므로 `"user"`로 인용

## 성능 최적화

### SQL 방식
- 배치 크기: 100개 문서
- 중복 처리: `ON CONFLICT DO NOTHING`
- 스키마 설정: `SET search_path TO garden4`

### Python 방식
- 배치 크기: 50개 문서
- 오류 처리: 개별 재시도
- 로깅: 진행 상황 실시간 출력

## 오류 처리

### 일반적인 오류와 해결법

1. **중복 키 오류**:
   ```
   duplicate key value violates unique constraint "slack_messages_ts_key"
   ```
   - 해결: `ON CONFLICT (ts) DO NOTHING` 사용

2. **JSON 파싱 오류**:
   ```
   Error parsing line: Expecting value: line 1 column 1 (char 0)
   ```
   - 해결: 빈 라인이나 잘못된 JSON 형식 확인

3. **타임스탬프 변환 오류**:
   ```
   Error converting timestamp
   ```
   - 해결: `$numberLong` 필드 존재 여부 확인

## 검증 방법

### 1. 데이터 개수 확인
```sql
-- MongoDB 원본
db.slack_messages.countDocuments({})

-- Supabase 결과
SELECT COUNT(*) FROM garden4.slack_messages;
```

### 2. 샘플 데이터 비교
```python
# Python으로 검증
import json
from supabase import create_client

# 원본 JSON 읽기
with open('slack_messages.json', 'r') as f:
    sample_doc = json.loads(f.readline())

# Supabase에서 조회
supabase = create_client(url, key)
result = supabase.schema('garden4').table('slack_messages')\
    .select('*').eq('ts', sample_doc['ts']).execute()

print(f"Original: {sample_doc}")
print(f"Migrated: {result.data[0]}")
```

### 3. 날짜 범위 쿼리 테스트
```sql
SELECT COUNT(*), 
       MIN(ts_for_db) as earliest,
       MAX(ts_for_db) as latest
FROM garden4.slack_messages
WHERE ts_for_db >= '2024-01-01'
  AND ts_for_db < '2025-01-01';
```

## 마이그레이션 체크리스트

### 사전 준비
- [ ] Supabase 프로젝트 생성
- [ ] 스키마 및 테이블 생성 (`supabase_schema.sql`)
- [ ] 환경 변수 설정 (`.env` 파일)
- [ ] Python 패키지 설치

### 데이터 변환
- [ ] JSON 파일 경로 확인
- [ ] 변환 스크립트 실행
- [ ] 오류 로그 확인
- [ ] 생성된 SQL 파일 검토

### 마이그레이션 실행
- [ ] SQL 실행 (방식 1) 또는 Python 스크립트 실행 (방식 2)
- [ ] 진행 상황 모니터링
- [ ] 오류 발생 시 개별 처리

### 사후 검증
- [ ] 데이터 개수 일치 확인
- [ ] 샘플 데이터 정합성 확인
- [ ] 날짜 범위 쿼리 테스트
- [ ] 애플리케이션 연동 테스트

## 롤백 계획
문제 발생 시:
1. Supabase 테이블 데이터 삭제: `DELETE FROM garden4.slack_messages;`
2. 원본 MongoDB 데이터로 복원
3. 변환 스크립트 수정 후 재실행

## 참고 파일
- `migration/json_to_sql.py`: SQL 변환 스크립트
- `migration/json_to_supabase.py`: 직접 삽입 스크립트  
- `migration/supabase_schema.sql`: 데이터베이스 스키마
- `migration/README.md`: 전체 마이그레이션 가이드