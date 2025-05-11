import os
import uuid
import csv
import sqlite3
import json
import io
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse



app = FastAPI(title="CSV to JSON API")

# API Key configuration
API_KEY = os.environ.get("API_KEY")
API_KEY_NAME = "x-api-key"


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    # Skip API key check for root endpoint (documentation)
    if request.url.path == "/" or request.url.path.startswith("/docs") or request.url.path.startswith("/openapi"):
        return await call_next(request)
        
    # Get API key from header
    api_key = request.headers.get(API_KEY_NAME)
    if api_key is None or api_key != API_KEY:
        return JSONResponse(
            status_code=403,
            content={"detail": "Invalid or missing API key"}
        )
    
    return await call_next(request)


# SQLite database setup
# Use an absolute path in a directory where www-data has write permissions
DATABASE_PATH = os.environ.get("DATABASE_PATH", "/home/ubuntu/csv/fastapi-csv/data")
os.makedirs(DATABASE_PATH, exist_ok=True)
DATABASE_NAME = os.path.join(DATABASE_PATH, "csv_data.db")


def get_db_connection():
    """Create a connection to the SQLite database"""
    # Ensure the database directory exists and has correct permissions
    os.makedirs(os.path.dirname(DATABASE_NAME), exist_ok=True)
    
    # Connect with write permissions
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    
    # Execute pragma for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")
    
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS counter (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        count INTEGER NOT NULL, 
        file_id TEXT NOT NULL,
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
async def get_csv_as_json(file_id: str):
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
        
        # add a counter to point to which row idx we are at
        cursor.execute("SELECT count FROM counter WHERE file_id = ?", (file_id,))
        row = cursor.fetchone()
        if row is None:
            cursor.execute("INSERT INTO counter (file_id, count) VALUES (?, 0)", (file_id,))
            conn.commit()
        else:
            cursor.execute("UPDATE counter SET count = count + 1 WHERE file_id = ?", (file_id,))
            conn.commit()
        
        # Query to get CSV data
        cursor.execute(
            "SELECT row_data FROM csv_data WHERE file_id = ? and row_index = ?", 
            (file_id, row[0])
        )
        
        # Process results
        result = []
        for row in cursor.fetchall():
            result.append(json.loads(row[0]))
        
        conn.close()
        return result
    
    except Exception as e:
        # Log the error for debugging
        print(f"Error retrieving CSV data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving CSV data: {str(e)}")


@app.get("/")
async def root():
    return {"message": "CSV to JSON API. Use /upload-csv/ to upload a CSV file and /get-csv/{id} to retrieve it as JSON."}

