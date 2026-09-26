#!/usr/bin/env python3
"""
Migrate JSON data (converted from BSON) to Supabase
"""

import json
import os
from datetime import datetime
from supabase import create_client, Client
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def transform_document(doc):
    """Transform MongoDB document to Supabase format"""
    
    # Handle the _id field
    if '_id' in doc and '$oid' in doc['_id']:
        del doc['_id']
    
    # Handle ts_for_db datetime
    if 'ts_for_db' in doc and '$date' in doc['ts_for_db']:
        if '$numberLong' in doc['ts_for_db']['$date']:
            timestamp_ms = int(doc['ts_for_db']['$date']['$numberLong'])
            doc['ts_for_db'] = datetime.fromtimestamp(timestamp_ms / 1000).isoformat()
        else:
            doc['ts_for_db'] = doc['ts_for_db']['$date']
    
    # Convert bot_profile to JSON string if it's a dict
    if 'bot_profile' in doc and isinstance(doc['bot_profile'], dict):
        doc['bot_profile'] = json.dumps(doc['bot_profile'])
    
    # Convert attachments to JSON string if it's a list
    if 'attachments' in doc and isinstance(doc['attachments'], list):
        # Handle $numberInt in attachments
        for attachment in doc['attachments']:
            if 'id' in attachment and isinstance(attachment['id'], dict) and '$numberInt' in attachment['id']:
                attachment['id'] = int(attachment['id']['$numberInt'])
        doc['attachments'] = json.dumps(doc['attachments'])
    
    # Handle updated field in bot_profile if needed
    if 'bot_profile' in doc and isinstance(doc['bot_profile'], str):
        try:
            bot_profile = json.loads(doc['bot_profile'])
            if 'updated' in bot_profile and isinstance(bot_profile['updated'], dict) and '$numberInt' in bot_profile['updated']:
                bot_profile['updated'] = int(bot_profile['updated']['$numberInt'])
                doc['bot_profile'] = json.dumps(bot_profile)
        except:
            pass
    
    return doc


def migrate_json_to_supabase(json_file_path, supabase_url, supabase_key):
    """Migrate JSON data to Supabase"""
    
    logger.info("Starting migration from JSON to Supabase...")
    
    # Initialize Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Read JSON file line by line (each line is a document)
    documents = []
    with open(json_file_path, 'r') as f:
        for line in f:
            try:
                doc = json.loads(line.strip())
                transformed = transform_document(doc)
                documents.append(transformed)
            except Exception as e:
                logger.error(f"Error parsing line: {e}")
                logger.error(f"Line: {line[:100]}...")
    
    logger.info(f"Loaded {len(documents)} documents")
    
    # Migrate in batches
    batch_size = 50
    success_count = 0
    error_count = 0
    duplicate_count = 0
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        
        try:
            # Try batch insert
            response = supabase.schema('garden4').table('slack_messages').insert(batch).execute()
            success_count += len(batch)
            logger.info(f"Progress: {success_count}/{len(documents)} migrated")
            
        except Exception as batch_error:
            logger.warning(f"Batch insert failed, trying individual inserts: {str(batch_error)[:100]}")
            
            # Try individual inserts
            for doc in batch:
                try:
                    response = supabase.schema('garden4').table('slack_messages').insert(doc).execute()
                    success_count += 1
                except Exception as e:
                    error_str = str(e)
                    if "duplicate key" in error_str or "already exists" in error_str:
                        duplicate_count += 1
                        logger.debug(f"Duplicate: {doc.get('ts')}")
                    else:
                        error_count += 1
                        logger.error(f"Error inserting document: {error_str[:100]}")
                        logger.error(f"Document ts: {doc.get('ts')}")
    
    # Final report
    logger.info("="*50)
    logger.info("Migration Complete!")
    logger.info(f"Total documents: {len(documents)}")
    logger.info(f"Successfully migrated: {success_count}")
    logger.info(f"Duplicates skipped: {duplicate_count}")
    logger.info(f"Errors: {error_count}")
    logger.info("="*50)
    
    # Verify count
    try:
        count_response = supabase.schema('garden4').table('slack_messages').select('*', count='exact').execute()
        logger.info(f"Total documents in Supabase: {count_response.count}")
    except Exception as e:
        logger.error(f"Error counting documents: {e}")


if __name__ == "__main__":
    # Get environment variables
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env file")
        logger.info("Create a .env file in the project root with:")
        logger.info('SUPABASE_URL=https://your-project.supabase.co')
        logger.info('SUPABASE_SERVICE_KEY=your-service-role-key')
        logger.info('')
        logger.info('You can copy .env.example and modify it')
        exit(1)
    
    json_file = "/Users/junho85/PycharmProjects/garden4/garden4-backend/20250622_mongodb_dump/garden/slack_messages.json"
    
    # Set schema path for garden4
    os.environ['PGRST_DB_SCHEMA'] = 'garden4'
    
    migrate_json_to_supabase(json_file, SUPABASE_URL, SUPABASE_SERVICE_KEY)