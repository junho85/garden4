#!/usr/bin/env python3
"""
Convert JSON dump to SQL INSERT statements for direct execution in Supabase
"""

import json
import re
from datetime import datetime

def escape_sql_string(value):
    """Escape string for SQL"""
    if value is None:
        return 'NULL'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict) or isinstance(value, list):
        # Convert to JSON string and escape
        json_str = json.dumps(value, ensure_ascii=False)
        # Escape single quotes
        json_str = json_str.replace("'", "''")
        return f"'{json_str}'"
    
    # String type
    str_value = str(value)
    # Escape single quotes
    str_value = str_value.replace("'", "''")
    return f"'{str_value}'"

def transform_document_to_sql(doc, batch_num, doc_num):
    """Transform MongoDB document to SQL INSERT"""
    
    # Handle the _id field - remove it
    if '_id' in doc:
        del doc['_id']
    
    # Handle ts_for_db datetime
    if 'ts_for_db' in doc and '$date' in doc['ts_for_db']:
        if '$numberLong' in doc['ts_for_db']['$date']:
            timestamp_ms = int(doc['ts_for_db']['$date']['$numberLong'])
            dt = datetime.fromtimestamp(timestamp_ms / 1000)
            doc['ts_for_db'] = dt.isoformat()
        else:
            doc['ts_for_db'] = doc['ts_for_db']['$date']
    
    # Handle $numberInt in bot_profile
    if 'bot_profile' in doc and isinstance(doc['bot_profile'], dict):
        if 'updated' in doc['bot_profile'] and isinstance(doc['bot_profile']['updated'], dict):
            if '$numberInt' in doc['bot_profile']['updated']:
                doc['bot_profile']['updated'] = int(doc['bot_profile']['updated']['$numberInt'])
    
    # Handle $numberInt in attachments
    if 'attachments' in doc and isinstance(doc['attachments'], list):
        for attachment in doc['attachments']:
            if 'id' in attachment and isinstance(attachment['id'], dict) and '$numberInt' in attachment['id']:
                attachment['id'] = int(attachment['id']['$numberInt'])
    
    # Build INSERT statement
    columns = ['ts', 'ts_for_db', 'bot_id', 'type', 'text', '"user"', 'team', 'bot_profile', 'attachments']
    values = []
    
    for col in columns:
        col_name = col.strip('"')  # Remove quotes for lookup
        if col_name in doc:
            values.append(escape_sql_string(doc[col_name]))
        else:
            values.append('NULL')
    
    return f"  ({', '.join(values)})"

def convert_json_to_sql(json_file_path, sql_file_path):
    """Convert JSON file to SQL INSERT statements"""
    
    print(f"Converting {json_file_path} to SQL...")
    
    # Read JSON file
    documents = []
    with open(json_file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                doc = json.loads(line.strip())
                documents.append(doc)
            except Exception as e:
                print(f"Error parsing line {line_num}: {e}")
    
    print(f"Loaded {len(documents)} documents")
    
    # Write SQL file
    with open(sql_file_path, 'w', encoding='utf-8') as f:
        f.write("-- MongoDB to Supabase Migration SQL\n")
        f.write("-- Execute this in Supabase SQL Editor\n\n")
        f.write("SET search_path TO garden4;\n\n")
        
        # Split into batches of 100 for better performance
        batch_size = 100
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(documents))
            batch = documents[start_idx:end_idx]
            
            f.write(f"-- Batch {batch_num + 1}/{total_batches} (Documents {start_idx + 1}-{end_idx})\n")
            f.write("INSERT INTO slack_messages (ts, ts_for_db, bot_id, type, text, \"user\", team, bot_profile, attachments)\nVALUES\n")
            
            value_lines = []
            for doc_num, doc in enumerate(batch):
                try:
                    value_line = transform_document_to_sql(doc, batch_num, doc_num)
                    value_lines.append(value_line)
                except Exception as e:
                    print(f"Error converting document in batch {batch_num}, doc {doc_num}: {e}")
                    print(f"Document ts: {doc.get('ts', 'unknown')}")
            
            f.write(',\n'.join(value_lines))
            f.write('\nON CONFLICT (ts) DO NOTHING;\n\n')
            
            # Add progress comment
            progress = ((batch_num + 1) / total_batches) * 100
            f.write(f"-- Progress: {progress:.1f}% complete\n\n")
    
    print(f"SQL file created: {sql_file_path}")
    print(f"Total documents: {len(documents)}")
    print(f"Total batches: {total_batches}")
    print("\nTo import:")
    print("1. Open Supabase SQL Editor")
    print("2. Copy and paste the SQL content")
    print("3. Execute the SQL")

if __name__ == "__main__":
    json_file = "/Users/junho85/PycharmProjects/garden4/garden4-backend/20250622_mongodb_dump/garden/slack_messages.json"
    sql_file = "/Users/junho85/PycharmProjects/garden4/garden4-backend/migration/slack_messages_import.sql"
    
    convert_json_to_sql(json_file, sql_file)