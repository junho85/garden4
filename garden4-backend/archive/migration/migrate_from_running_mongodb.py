#!/usr/bin/env python3
"""
Migrate data from running MongoDB instance to Supabase
"""

import os
from pymongo import MongoClient
from supabase import create_client
from datetime import datetime
import json
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def transform_mongodb_doc_to_supabase(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Transform MongoDB document to Supabase format"""
    
    # Create a copy to avoid modifying original
    transformed = {}
    
    # Copy basic fields
    for field in ['ts', 'bot_id', 'type', 'text', 'user', 'team']:
        if field in doc:
            transformed[field] = doc[field]
    
    # Handle ts_for_db
    if 'ts_for_db' in doc:
        if isinstance(doc['ts_for_db'], datetime):
            transformed['ts_for_db'] = doc['ts_for_db'].isoformat()
        else:
            transformed['ts_for_db'] = doc['ts_for_db']
    
    # Convert complex fields to JSON
    if 'bot_profile' in doc:
        transformed['bot_profile'] = json.dumps(doc['bot_profile'])
    
    if 'attachments' in doc:
        transformed['attachments'] = json.dumps(doc['attachments'])
    
    return transformed


def migrate_data(mongo_uri: str, mongo_db_name: str, supabase_url: str, supabase_key: str):
    """
    Migrate data from MongoDB to Supabase
    
    Args:
        mongo_uri: MongoDB connection URI
        mongo_db_name: MongoDB database name
        supabase_url: Supabase project URL
        supabase_key: Supabase service role key
    """
    
    # Connect to MongoDB
    logger.info("Connecting to MongoDB...")
    mongo_client = MongoClient(mongo_uri)
    mongo_db = mongo_client[mongo_db_name]
    collection = mongo_db['slack_messages']
    
    # Connect to Supabase
    logger.info("Connecting to Supabase...")
    supabase = create_client(supabase_url, supabase_key)
    
    # Count total documents
    total_count = collection.count_documents({})
    logger.info(f"Found {total_count} documents to migrate")
    
    # Migrate in batches
    batch_size = 100
    migrated_count = 0
    error_count = 0
    skip_count = 0
    
    # Use cursor with batch_size to avoid loading all data into memory
    cursor = collection.find({}).batch_size(batch_size)
    
    batch = []
    for doc in cursor:
        try:
            # Transform document
            transformed = transform_mongodb_doc_to_supabase(doc)
            batch.append(transformed)
            
            # Insert batch when full
            if len(batch) >= batch_size:
                try:
                    response = supabase.from_('garden4.slack_messages').insert(batch).execute()
                    migrated_count += len(batch)
                    logger.info(f"Progress: {migrated_count}/{total_count} migrated")
                    batch = []
                    
                except Exception as batch_error:
                    logger.error(f"Batch insert error: {batch_error}")
                    
                    # Try individual inserts for this batch
                    for individual_doc in batch:
                        try:
                            supabase.from_('garden4.slack_messages').insert(individual_doc).execute()
                            migrated_count += 1
                        except Exception as individual_error:
                            if "duplicate key" in str(individual_error):
                                skip_count += 1
                                logger.debug(f"Skipping duplicate: {individual_doc.get('ts')}")
                            else:
                                error_count += 1
                                logger.error(f"Individual insert error: {individual_error}")
                                logger.error(f"Document ts: {individual_doc.get('ts')}")
                    
                    batch = []
                    
        except Exception as e:
            error_count += 1
            logger.error(f"Transform error: {e}")
            logger.error(f"Document: {doc.get('_id')}")
    
    # Insert remaining documents
    if batch:
        try:
            response = supabase.from_('garden4.slack_messages').insert(batch).execute()
            migrated_count += len(batch)
        except Exception as e:
            logger.error(f"Final batch error: {e}")
            
            # Try individual inserts
            for doc in batch:
                try:
                    supabase.from_('garden4.slack_messages').insert(doc).execute()
                    migrated_count += 1
                except Exception as individual_error:
                    if "duplicate key" in str(individual_error):
                        skip_count += 1
                    else:
                        error_count += 1
                        logger.error(f"Individual insert error: {individual_error}")
    
    # Close MongoDB connection
    mongo_client.close()
    
    # Final report
    logger.info("="*50)
    logger.info("Migration Complete!")
    logger.info(f"Total documents: {total_count}")
    logger.info(f"Successfully migrated: {migrated_count}")
    logger.info(f"Skipped (duplicates): {skip_count}")
    logger.info(f"Errors: {error_count}")
    logger.info("="*50)
    
    # Verify count in Supabase
    try:
        count_response = supabase.from_('garden4.slack_messages').select('*', count='exact').execute()
        supabase_count = count_response.count
        logger.info(f"Documents in Supabase: {supabase_count}")
    except Exception as e:
        logger.error(f"Error counting Supabase documents: {e}")


def verify_migration(mongo_uri: str, mongo_db_name: str, supabase_url: str, supabase_key: str):
    """Verify migration by comparing sample data"""
    
    logger.info("Verifying migration...")
    
    # Connect to both databases
    mongo_client = MongoClient(mongo_uri)
    mongo_db = mongo_client[mongo_db_name]
    collection = mongo_db['slack_messages']
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Compare counts
    mongo_count = collection.count_documents({})
    supabase_response = supabase.from_('garden4.slack_messages').select('*', count='exact').execute()
    supabase_count = supabase_response.count
    
    logger.info(f"MongoDB count: {mongo_count}")
    logger.info(f"Supabase count: {supabase_count}")
    
    if mongo_count == supabase_count:
        logger.info("✓ Document counts match!")
    else:
        logger.warning(f"✗ Document count mismatch: MongoDB {mongo_count} vs Supabase {supabase_count}")
    
    # Compare sample documents
    sample_size = min(10, mongo_count)
    mongo_samples = list(collection.find().limit(sample_size))
    
    for mongo_doc in mongo_samples:
        ts = mongo_doc.get('ts')
        if ts:
            # Find in Supabase
            supabase_response = supabase.from_('garden4.slack_messages').select('*').eq('ts', ts).execute()
            
            if supabase_response.data:
                logger.info(f"✓ Found document with ts={ts}")
            else:
                logger.warning(f"✗ Missing document with ts={ts}")
    
    mongo_client.close()
    logger.info("Verification complete!")


if __name__ == "__main__":
    # Configuration from environment variables or defaults
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DB = os.getenv('MONGO_DB', 'garden')
    
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("Please set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables")
        exit(1)
    
    # Run migration
    migrate_data(MONGO_URI, MONGO_DB, SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Verify migration
    verify_migration(MONGO_URI, MONGO_DB, SUPABASE_URL, SUPABASE_SERVICE_KEY)