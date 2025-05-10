import os
import uuid
import csv
import sqlite3
import json
import io
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional

app = FastAPI(title="CSV to JSON API")

# SQLite database setup
DATABASE_NAME = "csv_data.db"


def get_db_connection():
    """Create a connection to the SQLite database"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn


# Initialize the database
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create table to store CSV file metadata
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS csv_files (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create table to store CSV data
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS csv_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id TEXT NOT NULL,
        row_index INTEGER NOT NULL,
        row_data TEXT NOT NULL,
        FOREIGN KEY (file_id) REFERENCES csv_files (id)
    )
    """)
    
    conn.commit()
    conn.close()


# Initialize the database on startup
init_db()


@app.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file and get a unique ID to access it later"""
    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # Generate a unique ID
    file_id = str(uuid.uuid4())
    
    # Read the file content
    content = await file.read()
    
    # Process CSV data
    try:
        # Decode the content
        text_content = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(text_content))
        
        # Get column names
        fieldnames = csv_reader.fieldnames
        if not fieldnames:
            raise HTTPException(status_code=400, detail="CSV file has no headers")
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Store file metadata
        cursor.execute(
            "INSERT INTO csv_files (id, filename) VALUES (?, ?)",
            (file_id, file.filename)
        )
        
        # Store each row of CSV data
        for row_index, row in enumerate(csv_reader):
            # Convert row to JSON string
            row_json = json.dumps(row)
            cursor.execute(
                "INSERT INTO csv_data (file_id, row_index, row_data) VALUES (?, ?, ?)",
                (file_id, row_index, row_json)
            )
        
        conn.commit()
        conn.close()
        
        return {"id": file_id, "message": "CSV file uploaded successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")


@app.get("/get-csv/{file_id}")
async def get_csv_as_json(file_id: str, limit: Optional[int] = None):
    """Get CSV data as JSON using the file ID"""
    try:
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if file exists
        cursor.execute("SELECT id FROM csv_files WHERE id = ?", (file_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="File not found")
        
        # Query to get CSV data
        if limit is not None and limit > 0:
            cursor.execute(
                "SELECT row_data FROM csv_data WHERE file_id = ? ORDER BY row_index LIMIT ?", 
                (file_id, limit)
            )
        else:
            cursor.execute(
                "SELECT row_data FROM csv_data WHERE file_id = ? ORDER BY row_index", 
                (file_id,)
            )
        
        # Process results
        result = []
        for row in cursor.fetchall():
            result.append(json.loads(row[0]))
        
        conn.close()
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving CSV data: {str(e)}")


@app.get("/")
async def root():
    return {"message": "CSV to JSON API. Use /upload-csv/ to upload a CSV file and /get-csv/{id} to retrieve it as JSON."}

