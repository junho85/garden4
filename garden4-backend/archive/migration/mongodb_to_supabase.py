#!/usr/bin/env python3
"""
MongoDB to Supabase Migration Script
Migrates slack_messages collection from MongoDB dump to Supabase PostgreSQL
"""

import json
import bson
from datetime import datetime
from supabase import create_client, Client
import os
from typing import List, Dict, Any
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MongoToSupabaseMigrator:
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialize the migrator with Supabase credentials
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key (for write access)
        """
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
    def read_bson_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Read BSON dump file and return list of documents
        
        Args:
            file_path: Path to BSON file
            
        Returns:
            List of documents from BSON file
        """
        documents = []
        
        try:
            with open(file_path, 'rb') as f:
                # BSON 파일 읽기
                while True:
                    try:
                        # BSON 문서 디코드
                        doc = bson.decode(f.read())
                        if doc:
                            documents.append(doc)
                        else:
                            break
                    except:
                        # 파일 끝이거나 오류 발생 시
                        break
                        
            logger.info(f"Successfully read {len(documents)} documents from {file_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Error reading BSON file: {e}")
            raise
            
    def transform_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform MongoDB document to Supabase format
        
        Args:
            doc: MongoDB document
            
        Returns:
            Transformed document for Supabase
        """
        try:
            # ObjectId를 string으로 변환
            if '_id' in doc and hasattr(doc['_id'], '__str__'):
                doc['_id'] = str(doc['_id'])
                
            # ts_for_db datetime 변환
            if 'ts_for_db' in doc and '$date' in doc['ts_for_db']:
                # MongoDB extended JSON format 처리
                if '$numberLong' in doc['ts_for_db']['$date']:
                    timestamp_ms = int(doc['ts_for_db']['$date']['$numberLong'])
                    doc['ts_for_db'] = datetime.fromtimestamp(timestamp_ms / 1000).isoformat()
                else:
                    doc['ts_for_db'] = doc['ts_for_db']['$date']
                    
            # attachments 배열 처리 (이미 JSON 형식이므로 그대로 유지)
            # bot_profile도 JSON 형식으로 유지
            
            # Supabase 테이블 구조에 맞게 변환
            supabase_doc = {
                'ts': doc.get('ts'),
                'ts_for_db': doc.get('ts_for_db'),
                'bot_id': doc.get('bot_id'),
                'type': doc.get('type'),
                'text': doc.get('text'),
                'user': doc.get('user'),
                'team': doc.get('team'),
                'bot_profile': json.dumps(doc.get('bot_profile')) if doc.get('bot_profile') else None,
                'attachments': json.dumps(doc.get('attachments')) if doc.get('attachments') else None
            }
            
            # None 값 제거
            supabase_doc = {k: v for k, v in supabase_doc.items() if v is not None}
            
            return supabase_doc
            
        except Exception as e:
            logger.error(f"Error transforming document: {e}")
            logger.error(f"Document: {doc}")
            raise
            
    def migrate_to_supabase(self, documents: List[Dict[str, Any]], batch_size: int = 100):
        """
        Migrate documents to Supabase in batches
        
        Args:
            documents: List of transformed documents
            batch_size: Number of documents to insert per batch
        """
        total = len(documents)
        success_count = 0
        error_count = 0
        
        for i in range(0, total, batch_size):
            batch = documents[i:i + batch_size]
            
            try:
                # Supabase에 배치 삽입
                response = self.supabase.from_('slack_messages').insert(batch).execute()
                
                success_count += len(batch)
                logger.info(f"Inserted batch {i//batch_size + 1}: {len(batch)} documents")
                
            except Exception as e:
                error_count += len(batch)
                logger.error(f"Error inserting batch {i//batch_size + 1}: {e}")
                
                # 개별 삽입 시도 (중복 키 등의 문제 해결)
                for doc in batch:
                    try:
                        self.supabase.from_('slack_messages').insert(doc).execute()
                        success_count += 1
                        error_count -= 1
                    except Exception as individual_error:
                        logger.error(f"Error inserting individual document: {individual_error}")
                        logger.error(f"Document ts: {doc.get('ts')}")
                        
        logger.info(f"Migration completed: {success_count} success, {error_count} errors out of {total} total")
        
    def run_migration(self, bson_file_path: str):
        """
        Run the complete migration process
        
        Args:
            bson_file_path: Path to MongoDB BSON dump file
        """
        logger.info("Starting MongoDB to Supabase migration...")
        
        # 1. BSON 파일 읽기
        documents = self.read_bson_file(bson_file_path)
        
        # 2. 문서 변환
        logger.info("Transforming documents...")
        transformed_docs = []
        for doc in documents:
            try:
                transformed = self.transform_document(doc)
                transformed_docs.append(transformed)
            except Exception as e:
                logger.error(f"Failed to transform document: {e}")
                
        logger.info(f"Successfully transformed {len(transformed_docs)} documents")
        
        # 3. Supabase로 마이그레이션
        logger.info("Migrating to Supabase...")
        self.migrate_to_supabase(transformed_docs)
        
        logger.info("Migration process completed!")


if __name__ == "__main__":
    # 환경 변수 또는 직접 설정
    SUPABASE_URL = os.getenv('SUPABASE_URL', 'YOUR_SUPABASE_URL')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', 'YOUR_SERVICE_ROLE_KEY')
    
    # BSON 파일 경로
    BSON_FILE = '/Users/junho85/PycharmProjects/garden4/garden4-backend/20250622_mongodb_dump/garden/slack_messages.bson'
    
    # 마이그레이션 실행
    migrator = MongoToSupabaseMigrator(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    migrator.run_migration(BSON_FILE)