from fastapi import FastAPI, HTTPException, Query, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import requests
from typing import Optional
from datetime import datetime, timedelta
import os
from io import StringIO
import msal

app = FastAPI(
    title="Data API for RapidAPI",
    description="API providing access to regularly updated CSV data",
    version="1.0.0"
)

# Add CORS middleware for RapidAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration - Set these as environment variables
CLIENT_ID = os.getenv("SHAREPOINT_CLIENT_ID")
CLIENT_SECRET = os.getenv("SHAREPOINT_CLIENT_SECRET")
TENANT_ID = os.getenv("SHAREPOINT_TENANT_ID")
SITE_ID = os.getenv("SHAREPOINT_SITE_ID")
FILE_PATH = os.getenv("SHAREPOINT_FILE_PATH")

# Cache configuration (6 hours since data updates weekly on Fridays)
CACHE_DURATION = timedelta(hours=6)
last_fetch_time = None
cached_data = None


def verify_rapidapi_request(request: Request):
    """Verify that the request is coming from RapidAPI"""
    # RapidAPI sends these headers with every request
    rapidapi_proxy_secret = request.headers.get("X-RapidAPI-Proxy-Secret")
    rapidapi_user = request.headers.get("X-RapidAPI-User")
    
    # Optional: Verify the proxy secret matches your RapidAPI secret
    expected_secret = os.getenv("RAPIDAPI_PROXY_SECRET")
    if expected_secret and rapidapi_proxy_secret != expected_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return rapidapi_user


def get_access_token():
    """Get access token for Microsoft Graph API"""
    authority = f"https://login.microsoftonline.com/{TENANT_ID}"
    app_auth = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=authority,
        client_credential=CLIENT_SECRET,
    )
    
    result = app_auth.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"]
    )
    
    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(f"Could not acquire token: {result.get('error_description')}")


def fetch_csv_from_sharepoint():
    """Fetch CSV file from SharePoint and return as DataFrame with caching"""
    global last_fetch_time, cached_data
    
    # Return cached data if still valid
    if cached_data is not None and last_fetch_time is not None:
        if datetime.now() - last_fetch_time < CACHE_DURATION:
            return cached_data
    
    try:
        # Get access token
        token = get_access_token()
        
        # Download file from SharePoint via Graph API
        graph_url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drive/root:{FILE_PATH}:/content"
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(graph_url, headers=headers)
        response.raise_for_status()
        
        # Parse CSV
        csv_content = StringIO(response.text)
        df = pd.read_csv(csv_content)
        
        # Update cache
        cached_data = df
        last_fetch_time = datetime.now()
        
        return df
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")


@app.get("/", tags=["Info"])
async def root():
    """API information and available endpoints"""
    return {
        "name": "Data API",
        "version": "1.0.0",
        "description": "Access to regularly updated dataset (updates every Friday)",
        "endpoints": {
            "GET /data": "Retrieve data with optional filtering and pagination",
            "GET /columns": "List all available data columns",
            "GET /stats": "Get dataset statistics",
            "GET /health": "Health check"
        },
        "data_last_updated": last_fetch_time.isoformat() if last_fetch_time else "Not yet loaded"
    }


@app.get("/health", tags=["Info"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_cached": cached_data is not None,
        "last_fetch": last_fetch_time.isoformat() if last_fetch_time else None
    }


@app.get("/columns", tags=["Data"])
async def get_columns(request: Request):
    """Get list of all available columns in the dataset"""
    verify_rapidapi_request(request)
    df = fetch_csv_from_sharepoint()
    
    return {
        "columns": df.columns.tolist(),
        "count": len(df.columns),
        "data_types": df.dtypes.astype(str).to_dict()
    }


@app.get("/stats", tags=["Data"])
async def get_stats(request: Request):
    """Get statistics about the dataset"""
    verify_rapidapi_request(request)
    df = fetch_csv_from_sharepoint()
    
    return {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": df.columns.tolist(),
        "last_updated": last_fetch_time.isoformat() if last_fetch_time else None,
        "next_update": "Every Friday",
        "data_types": df.dtypes.astype(str).to_dict()
    }


@app.get("/data", tags=["Data"])
async def get_data(
    request: Request,
    limit: Optional[int] = Query(100, description="Maximum rows to return (max 1000)", le=1000),
    offset: Optional[int] = Query(0, description="Number of rows to skip", ge=0),
    columns: Optional[str] = Query(None, description="Comma-separated column names to return"),
    sort_by: Optional[str] = Query(None, description="Column name to sort by"),
    sort_order: Optional[str] = Query("asc", description="Sort order: 'asc' or 'desc'"),
):
    """
    Retrieve data from the dataset with filtering and pagination
    
    **Parameters:**
    - **limit**: Maximum number of rows to return (default: 100, max: 1000)
    - **offset**: Number of rows to skip for pagination (default: 0)
    - **columns**: Specific columns to return (comma-separated)
    - **sort_by**: Column name to sort results by
    - **sort_order**: Sort direction - 'asc' or 'desc' (default: 'asc')
    
    **Example:**
    ```
    /data?limit=50&offset=0&columns=name,value&sort_by=name&sort_order=desc
    ```
    """
    verify_rapidapi_request(request)
    df = fetch_csv_from_sharepoint()
    
    total_rows = len(df)
    
    # Column selection
    if columns:
        requested_cols = [col.strip() for col in columns.split(",")]
        invalid_cols = [col for col in requested_cols if col not in df.columns]
        
        if invalid_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid columns: {invalid_cols}. Available: {df.columns.tolist()}"
            )
        
        df = df[requested_cols]
    
    # Sorting
    if sort_by:
        if sort_by not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort column: {sort_by}. Available: {df.columns.tolist()}"
            )
        
        ascending = sort_order.lower() == "asc"
        df = df.sort_values(by=sort_by, ascending=ascending)
    
    # Pagination
    df_page = df.iloc[offset:offset + limit]
    
    # Convert to JSON
    data = df_page.to_dict(orient="records")
    
    return {
        "success": True,
        "data": data,
        "pagination": {
            "total_rows": total_rows,
            "returned_rows": len(data),
            "offset": offset,
            "limit": limit,
            "has_more": offset + limit < total_rows
        },
        "last_updated": last_fetch_time.isoformat() if last_fetch_time else None
    }