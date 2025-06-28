"""
Example of modified Garden class using Supabase instead of MongoDB
This shows how to update the existing garden.py to use Supabase
"""

import os
from datetime import datetime
from attendance.supabase_adapter import SupabaseAdapter


class Garden:
    def __init__(self):
        # Supabase 설정 (환경 변수 또는 config에서 가져오기)
        supabase_url = os.getenv('SUPABASE_URL', 'YOUR_SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY', 'YOUR_ANON_KEY')
        
        # MongoDB 대신 Supabase adapter 사용
        self.db = SupabaseAdapter(supabase_url, supabase_key, schema='garden4')
        self.slack_messages = self.db  # 기존 코드 호환성을 위해
        
    def find_slack_messages(self, start_date, end_date=None):
        """
        기존 MongoDB 쿼리를 Supabase로 변환한 예제
        """
        query = {"ts_for_db": {"$gte": start_date}}
        if end_date:
            query["ts_for_db"]["$lt"] = end_date
            
        # 기존 MongoDB 스타일 쿼리가 그대로 작동
        return self.slack_messages.find(query, sort=[("ts", 1)])
        
    def find_slack_messages_by_user(self, user, start_date, end_date=None):
        """
        사용자별 메시지 조회
        """
        query = {
            "attachments.author_name": user,
            "ts_for_db": {"$gte": start_date}
        }
        if end_date:
            query["ts_for_db"]["$lt"] = end_date
            
        return self.slack_messages.find(query, sort=[("ts", 1)])
        
    def save_slack_message(self, message):
        """
        Slack 메시지 저장
        """
        # ts_for_db 필드 추가 (기존 로직 유지)
        if 'ts' in message:
            message['ts_for_db'] = datetime.fromtimestamp(float(message['ts']))
            
        try:
            # 중복 체크 후 저장
            existing = self.slack_messages.find_one({"ts": message['ts']})
            if not existing:
                return self.slack_messages.insert_one(message)
            else:
                # 업데이트
                return self.slack_messages.update_one(
                    {"ts": message['ts']},
                    {"$set": message}
                )
        except Exception as e:
            print(f"Error saving message: {e}")
            return None
            
    def collect_slack_messages(self, start_date, end_date):
        """
        Slack API에서 메시지 수집 후 저장
        """
        # 기존 Slack API 호출 로직...
        # messages = self.get_messages_from_slack_api(start_date, end_date)
        
        # 예제 메시지
        messages = [
            {
                'ts': '1234567890.123456',
                'bot_id': 'BNGD110UR',
                'type': 'message',
                'text': '',
                'user': 'UNR1ZN80N',
                'team': 'TNMAF3TT2',
                'attachments': [{
                    'author_name': 'junho85',
                    'text': 'Test commit message',
                    'fallback': '[junho85/TIL] Test commit'
                }]
            }
        ]
        
        # 메시지 저장
        saved_count = 0
        for message in messages:
            if self.save_slack_message(message):
                saved_count += 1
                
        return saved_count
        
    def get_attendance_by_date(self, date):
        """
        특정 날짜의 출석 정보 조회
        """
        start_date = datetime.combine(date, datetime.min.time())
        end_date = datetime.combine(date.replace(day=date.day + 1), datetime.min.time())
        
        messages = self.find_slack_messages(start_date, end_date)
        
        # 사용자별로 그룹화
        attendance = {}
        for msg in messages:
            if 'attachments' in msg:
                for attachment in msg['attachments']:
                    author = attachment.get('author_name')
                    if author:
                        if author not in attendance:
                            attendance[author] = []
                        attendance[author].append({
                            'ts': msg['ts'],
                            'ts_for_db': msg['ts_for_db'],
                            'message': attachment.get('text', ''),
                            'repository': attachment.get('footer', '')
                        })
                        
        return attendance
        
    def migrate_from_mongodb(self, mongodb_collection):
        """
        MongoDB에서 Supabase로 데이터 마이그레이션
        """
        # MongoDB에서 모든 문서 읽기
        cursor = mongodb_collection.find({})
        documents = list(cursor)
        
        # 배치로 Supabase에 삽입
        batch_size = 100
        migrated = 0
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            try:
                self.slack_messages.insert_many(batch)
                migrated += len(batch)
                print(f"Migrated {migrated}/{len(documents)} documents")
            except Exception as e:
                print(f"Error migrating batch: {e}")
                
        return migrated


# 사용 예제
if __name__ == "__main__":
    # Garden 인스턴스 생성 (Supabase 사용)
    garden = Garden()
    
    # 오늘 날짜의 출석 정보 조회
    from datetime import date
    today = date.today()
    attendance = garden.get_attendance_by_date(today)
    
    print(f"Today's attendance ({today}):")
    for user, commits in attendance.items():
        print(f"  {user}: {len(commits)} commits")
        for commit in commits:
            print(f"    - {commit['message'][:50]}...")