-- Supabase garden4 스키마 생성
CREATE SCHEMA IF NOT EXISTS garden4;

-- garden4 스키마로 전환
SET search_path TO garden4;

-- slack_messages 테이블 생성 (JSONB 방식으로 MongoDB 구조 유지)
CREATE TABLE slack_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ts VARCHAR(20) UNIQUE NOT NULL,
    ts_for_db TIMESTAMP NOT NULL,
    bot_id VARCHAR(20),
    type VARCHAR(20),
    text TEXT,
    "user" VARCHAR(20),  -- user는 예약어이므로 따옴표 사용
    team VARCHAR(20),
    bot_profile JSONB,
    attachments JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 자주 사용되는 쿼리를 위한 추가 인덱스
CREATE INDEX idx_ts_for_db_range ON slack_messages (ts_for_db);
CREATE INDEX idx_attachments_author ON slack_messages USING GIN ((attachments));

-- GitHub 사용자별 커밋 조회를 위한 함수형 인덱스
CREATE INDEX idx_author_names ON slack_messages USING GIN ((attachments -> 'author_name'));

-- View 생성: 커밋 정보를 쉽게 조회하기 위한 뷰
CREATE OR REPLACE VIEW commit_messages AS
SELECT 
    sm.id,
    sm.ts,
    sm.ts_for_db,
    attachment->>'author_name' as github_username,
    attachment->>'text' as commit_message,
    attachment->>'fallback' as fallback,
    attachment->>'footer' as repository,
    sm.created_at
FROM 
    slack_messages sm,
    LATERAL jsonb_array_elements(sm.attachments) as attachment
WHERE 
    sm.attachments IS NOT NULL;

-- RLS (Row Level Security) 정책 설정 (필요한 경우)
ALTER TABLE slack_messages ENABLE ROW LEVEL SECURITY;

-- 읽기 권한 정책 (인증된 사용자는 모두 읽을 수 있음)
CREATE POLICY "Read access for authenticated users" ON slack_messages
    FOR SELECT
    USING (auth.role() = 'authenticated');

-- 쓰기 권한 정책 (서비스 역할만 쓸 수 있음)
CREATE POLICY "Write access for service role only" ON slack_messages
    FOR ALL
    USING (auth.role() = 'service_role');