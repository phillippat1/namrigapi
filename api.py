from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
import os
from supabase import create_client, Client
from datetime import datetime

app = FastAPI(
    title="Data API for RapidAPI",
    description="Professional data API powered by Supabase",
    version="1.0.0"
)

# CORS middleware for RapidAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase configuration from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
RAPIDAPI_SECRET = os.getenv("RAPIDAPI_PROXY_SECRET")

# Initialize Supabase client
if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
    print("⚠️  Warning: Supabase credentials not configured")


def verify_rapidapi_request(request: Request):
    """Verify request is from RapidAPI (optional but recommended)"""
    if RAPIDAPI_SECRET:
        proxy_secret = request.headers.get("X-RapidAPI-Proxy-Secret")
        if proxy_secret != RAPIDAPI_SECRET:
            raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get RapidAPI user info (useful for analytics)
    rapidapi_user = request.headers.get("X-RapidAPI-User")
    rapidapi_subscription = request.headers.get("X-RapidAPI-Subscription")
    
    return {
        "user": rapidapi_user,
        "subscription": rapidapi_subscription
    }


@app.get("/", tags=["Info"])
async def root():
    """API information and available endpoints"""
    return {
        "name": "Data API for RapidAPI",
        "version": "1.0.0",
        "description": "Access regularly updated dataset via clean REST API",
        "update_schedule": "Every Friday",
        "endpoints": {
            "GET /": "API information",
            "GET /health": "Health check",
            "GET /data": "Retrieve data with filtering and pagination",
            "GET /columns": "List all available columns",
            "GET /stats": "Dataset statistics",
            "GET /search": "Search data with text query"
        },
        "documentation": "https://rapidapi.com/your-username/api/your-api-name",
        "support": "your-email@example.com"
    }


@app.get("/health", tags=["Info"])
async def health_check():
    """Health check endpoint for monitoring"""
    supabase_connected = supabase is not None
    
    if supabase_connected:
        try:
            # Test query to verify connection
            result = supabase.table("data").select("id", count="exact").limit(1).execute()
            data_available = result.count > 0 if hasattr(result, 'count') else len(result.data) > 0
        except Exception as e:
            data_available = False
            supabase_connected = False
    else:
        data_available = False
    
    return {
        "status": "healthy" if supabase_connected and data_available else "degraded",
        "timestamp": datetime.now().isoformat(),
        "supabase_connected": supabase_connected,
        "data_available": data_available
    }


@app.get("/columns", tags=["Data"])
async def get_columns(request: Request):
    """Get list of all available columns and their data types"""
    verify_rapidapi_request(request)
    
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        # Get a sample row to determine columns
        result = supabase.table("data").select("*").limit(1).execute()
        
        if not result.data:
            return {
                "columns": [],
                "message": "No data available yet"
            }
        
        # Extract column names from first row
        columns = list(result.data[0].keys())
        
        # Remove internal Supabase columns
        columns = [col for col in columns if col not in ['id', 'created_at']]
        
        return {
            "columns": columns,
            "count": len(columns),
            "includes_metadata": False
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching columns: {str(e)}")


@app.get("/stats", tags=["Data"])
async def get_stats(request: Request):
    """Get statistics about the dataset"""
    verify_rapidapi_request(request)
    
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        # Get total count
        result = supabase.table("data").select("*", count="exact").execute()
        total_rows = result.count if hasattr(result, 'count') else len(result.data)
        
        # Get column info
        if result.data:
            columns = [col for col in result.data[0].keys() if col not in ['id', 'created_at']]
        else:
            columns = []
        
        return {
            "total_rows": total_rows,
            "total_columns": len(columns),
            "columns": columns,
            "update_schedule": "Every Friday",
            "data_available": total_rows > 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@app.get("/data", tags=["Data"])
async def get_data(
    request: Request,
    limit: int = Query(100, description="Maximum rows to return", ge=1, le=1000),
    offset: int = Query(0, description="Number of rows to skip", ge=0),
    columns: Optional[str] = Query(None, description="Comma-separated column names to return"),
    sort_by: Optional[str] = Query(None, description="Column name to sort by"),
    sort_order: str = Query("asc", description="Sort order: 'asc' or 'desc'", regex="^(asc|desc)$"),
):
    """
    Retrieve data with optional filtering and pagination
    
    **Parameters:**
    - **limit**: Maximum number of rows (1-1000, default: 100)
    - **offset**: Number of rows to skip for pagination (default: 0)
    - **columns**: Specific columns to return (comma-separated)
    - **sort_by**: Column to sort results by
    - **sort_order**: Sort direction - 'asc' or 'desc' (default: 'asc')
    
    **Examples:**
    ```
    /data?limit=50
    /data?limit=20&offset=40
    /data?columns=name,value&sort_by=name&sort_order=desc
    ```
    """
    verify_rapidapi_request(request)
    
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        # Start building query
        query = supabase.table("data")
        
        # Select specific columns or all
        if columns:
            column_list = [col.strip() for col in columns.split(",")]
            # Add id for sorting purposes
            if 'id' not in column_list:
                column_list.append('id')
            select_str = ",".join(column_list)
        else:
            select_str = "*"
        
        query = query.select(select_str)
        
        # Apply sorting
        if sort_by:
            ascending = sort_order.lower() == "asc"
            query = query.order(sort_by, desc=not ascending)
        else:
            # Default sort by id
            query = query.order("id")
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        # Execute query
        result = query.execute()
        
        # Get total count for pagination info
        count_result = supabase.table("data").select("*", count="exact").execute()
        total_rows = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
        
        # Remove internal columns from response
        cleaned_data = []
        for row in result.data:
            cleaned_row = {k: v for k, v in row.items() if k not in ['created_at']}
            cleaned_data.append(cleaned_row)
        
        return {
            "success": True,
            "data": cleaned_data,
            "pagination": {
                "total_rows": total_rows,
                "returned_rows": len(cleaned_data),
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_rows
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")


@app.get("/search", tags=["Data"])
async def search_data(
    request: Request,
    query: str = Query(..., description="Search query text"),
    column: str = Query(..., description="Column to search in"),
    limit: int = Query(100, description="Maximum rows to return", ge=1, le=1000),
):
    """
    Search for text within a specific column
    
    **Parameters:**
    - **query**: Text to search for
    - **column**: Which column to search in
    - **limit**: Maximum number of results (1-1000, default: 100)
    
    **Example:**
    ```
    /search?query=texas&column=state&limit=50
    ```
    """
    verify_rapidapi_request(request)
    
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        # Search using ilike (case-insensitive pattern matching)
        result = supabase.table("data").select("*").ilike(column, f"%{query}%").limit(limit).execute()
        
        # Remove internal columns
        cleaned_data = []
        for row in result.data:
            cleaned_row = {k: v for k, v in row.items() if k not in ['created_at']}
            cleaned_data.append(cleaned_row)
        
        return {
            "success": True,
            "query": query,
            "column_searched": column,
            "results_count": len(cleaned_data),
            "data": cleaned_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return {
        "error": "Endpoint not found",
        "path": request.url.path,
        "available_endpoints": ["/", "/health", "/data", "/columns", "/stats", "/search"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
