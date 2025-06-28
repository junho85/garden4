#!/usr/bin/env python3
"""
Convert MongoDB BSON dump to JSON for easier processing
"""

import subprocess
import json
import os

def convert_bson_to_json(bson_file_path, json_file_path):
    """
    Convert BSON file to JSON using bsondump command
    """
    print(f"Converting {bson_file_path} to JSON...")
    
    # Use bsondump to convert BSON to JSON
    with open(json_file_path, 'w') as json_file:
        process = subprocess.Popen(
            ['bsondump', bson_file_path],
            stdout=json_file,
            stderr=subprocess.PIPE
        )
        
        _, stderr = process.communicate()
        
        if process.returncode != 0:
            print(f"Error converting BSON: {stderr.decode()}")
            return False
    
    print(f"Conversion complete: {json_file_path}")
    return True

if __name__ == "__main__":
    bson_path = "/Users/junho85/PycharmProjects/garden4/garden4-backend/20250622_mongodb_dump/garden/slack_messages.bson"
    json_path = "/Users/junho85/PycharmProjects/garden4/garden4-backend/20250622_mongodb_dump/garden/slack_messages.json"
    
    convert_bson_to_json(bson_path, json_path)