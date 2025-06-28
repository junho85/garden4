"""
Supabase Adapter for Garden4 Attendance System
Provides MongoDB-like interface for Supabase queries
"""

from supabase import create_client, Client
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


class SupabaseAdapter:
    """Adapter class to provide MongoDB-like interface for Supabase"""
    
    def __init__(self, supabase_url: str, supabase_key: str, schema: str = 'garden4'):
        """
        Initialize Supabase adapter
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anon or service key
            schema: Schema name (default: garden4)
        """
        self.client: Client = create_client(supabase_url, supabase_key)
        self.schema = schema
        # Set schema in table name
        self.table_name = f"{schema}.slack_messages"
        
    def find(self, query: Dict[str, Any] = None, sort: List[tuple] = None, limit: int = None) -> List[Dict[str, Any]]:
        """
        Find documents matching query criteria
        
        Args:
            query: Query criteria (MongoDB-style)
            sort: Sort criteria as list of (field, direction) tuples
            limit: Maximum number of documents to return
            
        Returns:
            List of matching documents
        """
        try:
            # Start query
            query_builder = self.client.from_(self.table_name).select('*')
            
            # Apply query filters
            if query:
                for field, condition in query.items():
                    if isinstance(condition, dict):
                        # Handle MongoDB operators
                        if '$gte' in condition and '$lt' in condition:
                            # Range query
                            query_builder = query_builder.gte(field, condition['$gte'])
                            query_builder = query_builder.lt(field, condition['$lt'])
                        elif '$gte' in condition:
                            query_builder = query_builder.gte(field, condition['$gte'])
                        elif '$lt' in condition:
                            query_builder = query_builder.lt(field, condition['$lt'])
                        elif '$gt' in condition:
                            query_builder = query_builder.gt(field, condition['$gt'])
                        elif '$lte' in condition:
                            query_builder = query_builder.lte(field, condition['$lte'])
                    elif field.startswith('attachments.'):
                        # Handle nested JSON queries
                        # For attachments.author_name queries
                        json_path = field.replace('.', '->')
                        query_builder = query_builder.filter(f"{json_path}", 'cs', f'"{condition}"')
                    else:
                        # Exact match
                        query_builder = query_builder.eq(field, condition)
            
            # Apply sorting
            if sort:
                for field, direction in sort:
                    ascending = direction == 1
                    query_builder = query_builder.order(field, desc=not ascending)
            
            # Apply limit
            if limit:
                query_builder = query_builder.limit(limit)
            
            # Execute query
            response = query_builder.execute()
            
            # Transform results
            documents = []
            for row in response.data:
                doc = self._transform_row_to_document(row)
                documents.append(doc)
                
            return documents
            
        except Exception as e:
            logger.error(f"Error executing find query: {e}")
            return []
            
    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find single document matching query criteria
        
        Args:
            query: Query criteria
            
        Returns:
            Matching document or None
        """
        results = self.find(query, limit=1)
        return results[0] if results else None
        
    def insert_one(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert single document
        
        Args:
            document: Document to insert
            
        Returns:
            Inserted document
        """
        try:
            # Transform document for Supabase
            supabase_doc = self._transform_document_for_insert(document)
            
            # Insert
            response = self.client.from_(self.table_name).insert(supabase_doc).execute()
            
            if response.data:
                return self._transform_row_to_document(response.data[0])
            else:
                raise Exception("Insert failed")
                
        except Exception as e:
            logger.error(f"Error inserting document: {e}")
            raise
            
    def insert_many(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Insert multiple documents
        
        Args:
            documents: List of documents to insert
            
        Returns:
            List of inserted documents
        """
        try:
            # Transform documents
            supabase_docs = [self._transform_document_for_insert(doc) for doc in documents]
            
            # Batch insert
            response = self.client.from_(self.table_name).insert(supabase_docs).execute()
            
            # Transform results back
            inserted = []
            for row in response.data:
                inserted.append(self._transform_row_to_document(row))
                
            return inserted
            
        except Exception as e:
            logger.error(f"Error inserting documents: {e}")
            return []
            
    def update_one(self, query: Dict[str, Any], update: Dict[str, Any]) -> bool:
        """
        Update single document matching query
        
        Args:
            query: Query criteria
            update: Update operations
            
        Returns:
            True if successful
        """
        try:
            # Find document to update
            doc = self.find_one(query)
            if not doc:
                return False
                
            # Apply update
            if '$set' in update:
                update_data = update['$set']
            else:
                update_data = update
                
            # Transform for Supabase
            supabase_update = self._transform_document_for_insert(update_data)
            
            # Update by ts (unique key)
            response = self.client.from_(self.table_name).update(supabase_update).eq('ts', doc['ts']).execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return False
            
    def delete_many(self, query: Dict[str, Any]) -> int:
        """
        Delete documents matching query
        
        Args:
            query: Query criteria
            
        Returns:
            Number of deleted documents
        """
        try:
            # Build delete query
            query_builder = self.client.from_(self.table_name).delete()
            
            # Apply filters
            for field, value in query.items():
                if isinstance(value, dict):
                    # Handle operators
                    for op, val in value.items():
                        if op == '$gte':
                            query_builder = query_builder.gte(field, val)
                        elif op == '$lt':
                            query_builder = query_builder.lt(field, val)
                else:
                    query_builder = query_builder.eq(field, value)
                    
            # Execute delete
            response = query_builder.execute()
            
            return len(response.data)
            
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return 0
            
    def count_documents(self, query: Dict[str, Any] = None) -> int:
        """
        Count documents matching query
        
        Args:
            query: Query criteria
            
        Returns:
            Count of matching documents
        """
        try:
            # Use select with count
            query_builder = self.client.from_(self.table_name).select('*', count='exact')
            
            # Apply query filters (same as find method)
            if query:
                for field, condition in query.items():
                    if isinstance(condition, dict):
                        for op, val in condition.items():
                            if op == '$gte':
                                query_builder = query_builder.gte(field, val)
                            elif op == '$lt':
                                query_builder = query_builder.lt(field, val)
                    else:
                        query_builder = query_builder.eq(field, condition)
                        
            response = query_builder.execute()
            
            return response.count if response.count is not None else 0
            
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0
            
    def _transform_document_for_insert(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Transform MongoDB-style document for Supabase insert"""
        supabase_doc = doc.copy()
        
        # Remove _id if present
        if '_id' in supabase_doc:
            del supabase_doc['_id']
            
        # Convert datetime objects to ISO format
        if 'ts_for_db' in supabase_doc and isinstance(supabase_doc['ts_for_db'], datetime):
            supabase_doc['ts_for_db'] = supabase_doc['ts_for_db'].isoformat()
            
        # Convert dicts/lists to JSON strings for JSONB columns
        if 'attachments' in supabase_doc and isinstance(supabase_doc['attachments'], list):
            supabase_doc['attachments'] = json.dumps(supabase_doc['attachments'])
            
        if 'bot_profile' in supabase_doc and isinstance(supabase_doc['bot_profile'], dict):
            supabase_doc['bot_profile'] = json.dumps(supabase_doc['bot_profile'])
            
        return supabase_doc
        
    def _transform_row_to_document(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Supabase row to MongoDB-style document"""
        doc = row.copy()
        
        # Parse JSON fields
        if 'attachments' in doc and isinstance(doc['attachments'], str):
            try:
                doc['attachments'] = json.loads(doc['attachments'])
            except:
                pass
                
        if 'bot_profile' in doc and isinstance(doc['bot_profile'], str):
            try:
                doc['bot_profile'] = json.loads(doc['bot_profile'])
            except:
                pass
                
        # Convert timestamp strings to datetime
        if 'ts_for_db' in doc and isinstance(doc['ts_for_db'], str):
            try:
                doc['ts_for_db'] = datetime.fromisoformat(doc['ts_for_db'].replace('Z', '+00:00'))
            except:
                pass
                
        # Add _id field for compatibility (using id)
        if 'id' in doc:
            doc['_id'] = doc['id']
            
        return doc
        
    def create_index(self, keys: List[tuple], **kwargs):
        """Placeholder for index creation (handled by SQL schema)"""
        logger.info(f"Index creation handled by SQL schema: {keys}")
        pass