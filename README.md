# FastAPI CSV to JSON API

A simple API to upload CSV files and retrieve their data as JSON using SQLite for storage.

## Features

- Upload CSV files and get a unique ID
- Store CSV data in SQLite database
- Retrieve CSV data as JSON using the ID
- Optional row limit parameter for large files

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Run the application:

```bash
uvicorn app:app --reload
```

## API Endpoints

### Upload a CSV File

**Endpoint:** `POST /upload-csv/`

**Request:** Form data with a CSV file

**Response:** JSON with a unique ID for the uploaded file

```json
{
  "id": "uuid-string",
  "message": "CSV file uploaded successfully"
}
```

### Get CSV Data as JSON

**Endpoint:** `GET /get-csv/{file_id}`

**Parameters:**
- `file_id`: The unique ID returned from the upload endpoint
- `limit` (optional): Maximum number of rows to return

**Response:** JSON array of objects representing the CSV data

## Example Usage

### Using curl

Upload a CSV file:
```bash
curl -X POST -F "file=@your_file.csv" http://localhost:8000/upload-csv/
```

Get the data as JSON:
```bash
curl http://localhost:8000/get-csv/your-file-id
```

With row limit:
```bash
curl http://localhost:8000/get-csv/your-file-id?limit=10
```

### Using the Swagger UI

You can also use the built-in Swagger UI at http://localhost:8000/docs to interact with the API.

## Running as a Linux Service

This application can be set up to run as a systemd service on Linux systems.

### Installation Steps

1. Clone this repository to your Linux server

2. Run the installation script with sudo:

```bash
sudo ./install_service.sh
```

This script will:
- Create a Python virtual environment
- Install all dependencies
- Configure the systemd service with the correct paths
- Enable and start the service

### Managing the Service

Check service status:
```bash
systemctl status fastapi-csv.service
```

Restart the service:
```bash
sudo systemctl restart fastapi-csv.service
```

Stop the service:
```bash
sudo systemctl stop fastapi-csv.service
```

View logs:
```bash
journalctl -u fastapi-csv.service
```
