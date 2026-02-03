"""
Baker Hughes Weekly Rig Count API
Flask REST API for serving rig count data from CSV
Tailored for AES data analysis and forecasting
"""

from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import pandas as pd
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
CSV_FILE_PATH = os.environ.get('CSV_PATH', 'Baker_Hughes_Weekly.csv')
API_KEY = os.environ.get('API_KEY', None)  # Optional API key protection

# Global dataframe cache
_df_cache = None
_last_loaded = None

def load_data(force_reload=False):
    """Load CSV data with caching"""
    global _df_cache, _last_loaded
    
    if _df_cache is None or force_reload:
        try:
            _df_cache = pd.read_csv(CSV_FILE_PATH, encoding='utf-8-sig')  # Handle BOM
            _last_loaded = datetime.now()
            
            # Clean column names (remove any leading/trailing whitespace)
            _df_cache.columns = _df_cache.columns.str.strip()
            
            # Convert date column
            if 'US_PublishDate' in _df_cache.columns:
                _df_cache['US_PublishDate'] = pd.to_datetime(_df_cache['US_PublishDate'])
                    
            print(f"Loaded {len(_df_cache)} rows from {CSV_FILE_PATH}")
        except FileNotFoundError:
            print(f"Error: CSV file not found at {CSV_FILE_PATH}")
            _df_cache = pd.DataFrame()
        except Exception as e:
            print(f"Error loading CSV: {e}")
            _df_cache = pd.DataFrame()
    
    return _df_cache

def require_api_key(f):
    """Decorator for optional API key authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if API_KEY:
            key = request.headers.get('X-API-Key') or request.args.get('api_key')
            if key != API_KEY:
                abort(401, description="Invalid or missing API key")
        return f(*args, **kwargs)
    return decorated

def serialize_records(df):
    """Convert DataFrame to JSON-serializable records"""
    records = df.to_dict(orient='records')
    for record in records:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, pd.Timestamp):
                record[key] = value.strftime('%Y-%m-%d')
    return records

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/')
def home():
    """API documentation endpoint"""
    return jsonify({
        "name": "Baker Hughes Weekly Rig Count API",
        "version": "2.0.0",
        "data_columns": [
            "Source.Name", "Country", "County", "Basin", "GOM", 
            "DrillFor", "Location", "State/Province", "Trajectory",
            "Year", "Month", "US_PublishDate", "Rig Count Value"
        ],
        "endpoints": {
            "GET /": "This documentation",
            "GET /health": "Health check",
            "GET /data": "Get all rig count data (paginated)",
            "GET /data/columns": "List available columns with metadata",
            "GET /data/summary": "Get summary statistics",
            "GET /data/filter": "Filter data by any column",
            "GET /data/latest": "Get most recent data",
            "GET /data/date-range": "Get data within date range",
            "GET /aggregate/by-state": "Rig counts aggregated by state",
            "GET /aggregate/by-basin": "Rig counts aggregated by basin",
            "GET /aggregate/by-country": "Rig counts aggregated by country",
            "GET /aggregate/by-date": "Rig counts aggregated by publish date",
            "GET /aggregate/time-series": "Time series for specific filters",
            "GET /unique/<column>": "Get unique values for a column",
            "POST /reload": "Reload CSV data from file"
        },
        "filter_examples": {
            "by_state": "/data/filter?State/Province=TEXAS",
            "by_basin": "/data/filter?Basin=Permian",
            "by_drill_type": "/data/filter?DrillFor=Oil",
            "by_trajectory": "/data/filter?Trajectory=Horizontal",
            "combined": "/data/filter?Country=UNITED STATES&DrillFor=Oil&Basin=Permian"
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    df = load_data()
    return jsonify({
        "status": "healthy",
        "rows_loaded": len(df),
        "last_loaded": _last_loaded.isoformat() if _last_loaded else None,
        "csv_path": CSV_FILE_PATH,
        "date_range": {
            "min": df['US_PublishDate'].min().strftime('%Y-%m-%d') if not df.empty else None,
            "max": df['US_PublishDate'].max().strftime('%Y-%m-%d') if not df.empty else None
        } if 'US_PublishDate' in df.columns else None
    })

@app.route('/data')
@require_api_key
def get_all_data():
    """Get all data with pagination"""
    df = load_data()
    
    if df.empty:
        return jsonify({"error": "No data loaded", "data": []}), 404
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 100, type=int), 1000)
    
    # Sorting
    sort_by = request.args.get('sort_by', 'US_PublishDate')
    sort_order = request.args.get('sort_order', 'desc')
    
    if sort_by and sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=(sort_order == 'asc'))
    
    # Calculate pagination
    total = len(df)
    start = (page - 1) * per_page
    end = start + per_page
    
    page_data = df.iloc[start:end]
    
    return jsonify({
        "data": serialize_records(page_data),
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
            "has_next": end < total,
            "has_prev": page > 1
        }
    })

@app.route('/data/columns')
@require_api_key
def get_columns():
    """Get list of available columns with data types and unique values"""
    df = load_data()
    
    if df.empty:
        return jsonify({"error": "No data loaded"}), 404
    
    columns = []
    for col in df.columns:
        col_info = {
            "name": col,
            "dtype": str(df[col].dtype),
            "non_null_count": int(df[col].notna().sum()),
            "unique_count": int(df[col].nunique())
        }
        
        # Add unique values for categorical columns
        if df[col].dtype == 'object' and df[col].nunique() <= 50:
            col_info["unique_values"] = sorted(df[col].dropna().unique().tolist())
        elif pd.api.types.is_numeric_dtype(df[col]):
            col_info["min"] = float(df[col].min()) if not pd.isna(df[col].min()) else None
            col_info["max"] = float(df[col].max()) if not pd.isna(df[col].max()) else None
            
        columns.append(col_info)
    
    return jsonify({"columns": columns, "total_columns": len(columns)})

@app.route('/data/summary')
@require_api_key
def get_summary():
    """Get summary statistics"""
    df = load_data()
    
    if df.empty:
        return jsonify({"error": "No data loaded"}), 404
    
    summary = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "date_range": {
            "min": df['US_PublishDate'].min().strftime('%Y-%m-%d'),
            "max": df['US_PublishDate'].max().strftime('%Y-%m-%d')
        },
        "total_rig_count_records": int(df['Rig Count Value'].sum()),
        "countries": df['Country'].nunique(),
        "states_provinces": df['State/Province'].nunique(),
        "basins": df['Basin'].nunique(),
        "counties": df['County'].nunique(),
        "breakdown": {
            "by_country": df.groupby('Country')['Rig Count Value'].sum().to_dict(),
            "by_drill_type": df.groupby('DrillFor')['Rig Count Value'].sum().to_dict(),
            "by_trajectory": df.groupby('Trajectory')['Rig Count Value'].sum().to_dict(),
            "by_location": df.groupby('Location')['Rig Count Value'].sum().to_dict()
        }
    }
    
    return jsonify(summary)

@app.route('/data/filter')
@require_api_key
def filter_data():
    """
    Filter data by any column
    Usage: /data/filter?Column=value&Column2=value2
    Supports: exact match, contains (*value*), greater than (>value), less than (<value)
    """
    df = load_data()
    
    if df.empty:
        return jsonify({"error": "No data loaded"}), 404
    
    filtered_df = df.copy()
    
    # Get all query parameters except pagination/sorting
    exclude_params = ['page', 'per_page', 'sort_by', 'sort_order', 'format', 'api_key']
    
    for param, value in request.args.items():
        if param in exclude_params:
            continue
            
        if param not in df.columns:
            continue
        
        # Handle different filter types
        if value.startswith('*') and value.endswith('*'):
            search_term = value[1:-1]
            filtered_df = filtered_df[filtered_df[param].astype(str).str.contains(search_term, case=False, na=False)]
        elif value.startswith('>='):
            try:
                num_value = float(value[2:])
                filtered_df = filtered_df[pd.to_numeric(filtered_df[param], errors='coerce') >= num_value]
            except ValueError:
                pass
        elif value.startswith('<='):
            try:
                num_value = float(value[2:])
                filtered_df = filtered_df[pd.to_numeric(filtered_df[param], errors='coerce') <= num_value]
            except ValueError:
                pass
        elif value.startswith('>'):
            try:
                num_value = float(value[1:])
                filtered_df = filtered_df[pd.to_numeric(filtered_df[param], errors='coerce') > num_value]
            except ValueError:
                pass
        elif value.startswith('<'):
            try:
                num_value = float(value[1:])
                filtered_df = filtered_df[pd.to_numeric(filtered_df[param], errors='coerce') < num_value]
            except ValueError:
                pass
        else:
            filtered_df = filtered_df[filtered_df[param].astype(str) == value]
    
    # Apply pagination
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 100, type=int), 1000)
    
    # Sorting
    sort_by = request.args.get('sort_by', 'US_PublishDate')
    sort_order = request.args.get('sort_order', 'desc')
    
    if sort_by and sort_by in filtered_df.columns:
        filtered_df = filtered_df.sort_values(by=sort_by, ascending=(sort_order == 'asc'))
    
    total = len(filtered_df)
    start = (page - 1) * per_page
    end = start + per_page
    
    page_data = filtered_df.iloc[start:end]
    
    return jsonify({
        "data": serialize_records(page_data),
        "filters_applied": {k: v for k, v in request.args.items() if k not in exclude_params and k in df.columns},
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0
        }
    })

@app.route('/data/latest')
@require_api_key
def get_latest():
    """Get the most recent rig count data"""
    df = load_data()
    
    if df.empty:
        return jsonify({"error": "No data loaded"}), 404
    
    n = request.args.get('n', 100, type=int)
    latest_date = df['US_PublishDate'].max()
    
    # Get data from the latest publish date
    latest = df[df['US_PublishDate'] == latest_date].head(n)
    
    return jsonify({
        "data": serialize_records(latest),
        "latest_date": latest_date.strftime('%Y-%m-%d'),
        "count": len(latest)
    })

@app.route('/data/date-range')
@require_api_key
def get_date_range():
    """
    Get data within a date range
    Usage: /data/date-range?start=2024-01-01&end=2024-12-31
    """
    df = load_data()
    
    if df.empty:
        return jsonify({"error": "No data loaded"}), 404
    
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    if not start_date and not end_date:
        return jsonify({"error": "Please provide 'start' and/or 'end' date parameters (YYYY-MM-DD)"}), 400
    
    filtered_df = df.copy()
    
    try:
        if start_date:
            filtered_df = filtered_df[filtered_df['US_PublishDate'] >= pd.to_datetime(start_date)]
        if end_date:
            filtered_df = filtered_df[filtered_df['US_PublishDate'] <= pd.to_datetime(end_date)]
    except Exception as e:
        return jsonify({"error": f"Date parsing error: {str(e)}"}), 400
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 100, type=int), 1000)
    
    total = len(filtered_df)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    page_data = filtered_df.iloc[start_idx:end_idx]
    
    return jsonify({
        "data": serialize_records(page_data),
        "date_range": {"start": start_date, "end": end_date},
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0
        }
    })

# ============================================
# AGGREGATION ENDPOINTS
# ============================================

@app.route('/aggregate/by-state')
@require_api_key
def aggregate_by_state():
    """Get rig counts aggregated by state/province"""
    df = load_data()
    
    if df.empty:
        return jsonify({"error": "No data loaded"}), 404
    
    # Optional filters
    country = request.args.get('country')
    date = request.args.get('date')  # Single date
    drill_for = request.args.get('drill_for')
    
    filtered_df = df.copy()
    
    if country:
        filtered_df = filtered_df[filtered_df['Country'] == country]
    if date:
        filtered_df = filtered_df[filtered_df['US_PublishDate'] == pd.to_datetime(date)]
    if drill_for:
        filtered_df = filtered_df[filtered_df['DrillFor'] == drill_for]
    
    # If no date specified, use the latest date
    if not date:
        latest_date = filtered_df['US_PublishDate'].max()
        filtered_df = filtered_df[filtered_df['US_PublishDate'] == latest_date]
        date = latest_date.strftime('%Y-%m-%d')
    
    agg = filtered_df.groupby(['Country', 'State/Province']).agg({
        'Rig Count Value': 'sum'
    }).reset_index()
    
    agg = agg.sort_values('Rig Count Value', ascending=False)
    
    return jsonify({
        "data": agg.to_dict(orient='records'),
        "date": date,
        "total_rigs": int(agg['Rig Count Value'].sum()),
        "filters": {"country": country, "drill_for": drill_for}
    })

@app.route('/aggregate/by-basin')
@require_api_key
def aggregate_by_basin():
    """Get rig counts aggregated by basin"""
    df = load_data()
    
    if df.empty:
        return jsonify({"error": "No data loaded"}), 404
    
    # Optional filters
    country = request.args.get('country')
    date = request.args.get('date')
    drill_for = request.args.get('drill_for')
    
    filtered_df = df.copy()
    
    if country:
        filtered_df = filtered_df[filtered_df['Country'] == country]
    if date:
        filtered_df = filtered_df[filtered_df['US_PublishDate'] == pd.to_datetime(date)]
    if drill_for:
        filtered_df = filtered_df[filtered_df['DrillFor'] == drill_for]
    
    # If no date specified, use the latest date
    if not date:
        latest_date = filtered_df['US_PublishDate'].max()
        filtered_df = filtered_df[filtered_df['US_PublishDate'] == latest_date]
        date = latest_date.strftime('%Y-%m-%d')
    
    agg = filtered_df.groupby('Basin').agg({
        'Rig Count Value': 'sum'
    }).reset_index()
    
    agg = agg.sort_values('Rig Count Value', ascending=False)
    
    return jsonify({
        "data": agg.to_dict(orient='records'),
        "date": date,
        "total_rigs": int(agg['Rig Count Value'].sum()),
        "filters": {"country": country, "drill_for": drill_for}
    })

@app.route('/aggregate/by-country')
@require_api_key
def aggregate_by_country():
    """Get rig counts aggregated by country"""
    df = load_data()
    
    if df.empty:
        return jsonify({"error": "No data loaded"}), 404
    
    date = request.args.get('date')
    drill_for = request.args.get('drill_for')
    
    filtered_df = df.copy()
    
    if date:
        filtered_df = filtered_df[filtered_df['US_PublishDate'] == pd.to_datetime(date)]
    if drill_for:
        filtered_df = filtered_df[filtered_df['DrillFor'] == drill_for]
    
    # If no date specified, use the latest date
    if not date:
        latest_date = filtered_df['US_PublishDate'].max()
        filtered_df = filtered_df[filtered_df['US_PublishDate'] == latest_date]
        date = latest_date.strftime('%Y-%m-%d')
    
    agg = filtered_df.groupby('Country').agg({
        'Rig Count Value': 'sum'
    }).reset_index()
    
    agg = agg.sort_values('Rig Count Value', ascending=False)
    
    return jsonify({
        "data": agg.to_dict(orient='records'),
        "date": date,
        "total_rigs": int(agg['Rig Count Value'].sum()),
        "filters": {"drill_for": drill_for}
    })

@app.route('/aggregate/by-date')
@require_api_key
def aggregate_by_date():
    """Get total rig counts aggregated by publish date (time series)"""
    df = load_data()
    
    if df.empty:
        return jsonify({"error": "No data loaded"}), 404
    
    # Optional filters
    country = request.args.get('country')
    state = request.args.get('state')
    basin = request.args.get('basin')
    drill_for = request.args.get('drill_for')
    trajectory = request.args.get('trajectory')
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    filtered_df = df.copy()
    
    if country:
        filtered_df = filtered_df[filtered_df['Country'] == country]
    if state:
        filtered_df = filtered_df[filtered_df['State/Province'] == state]
    if basin:
        filtered_df = filtered_df[filtered_df['Basin'] == basin]
    if drill_for:
        filtered_df = filtered_df[filtered_df['DrillFor'] == drill_for]
    if trajectory:
        filtered_df = filtered_df[filtered_df['Trajectory'] == trajectory]
    if start_date:
        filtered_df = filtered_df[filtered_df['US_PublishDate'] >= pd.to_datetime(start_date)]
    if end_date:
        filtered_df = filtered_df[filtered_df['US_PublishDate'] <= pd.to_datetime(end_date)]
    
    agg = filtered_df.groupby('US_PublishDate').agg({
        'Rig Count Value': 'sum'
    }).reset_index()
    
    agg = agg.sort_values('US_PublishDate')
    agg['US_PublishDate'] = agg['US_PublishDate'].dt.strftime('%Y-%m-%d')
    
    return jsonify({
        "data": agg.to_dict(orient='records'),
        "data_points": len(agg),
        "filters": {
            "country": country, "state": state, "basin": basin,
            "drill_for": drill_for, "trajectory": trajectory,
            "start": start_date, "end": end_date
        }
    })

@app.route('/aggregate/time-series')
@require_api_key
def time_series():
    """
    Get time series data with flexible grouping
    Usage: /aggregate/time-series?group_by=Basin&country=UNITED STATES
    """
    df = load_data()
    
    if df.empty:
        return jsonify({"error": "No data loaded"}), 404
    
    group_by = request.args.get('group_by', 'Country')  # What to group by besides date
    
    # Validate group_by
    valid_groups = ['Country', 'State/Province', 'Basin', 'DrillFor', 'Trajectory', 'Location']
    if group_by not in valid_groups:
        return jsonify({"error": f"Invalid group_by. Must be one of: {valid_groups}"}), 400
    
    # Optional filters
    country = request.args.get('country')
    state = request.args.get('state')
    basin = request.args.get('basin')
    drill_for = request.args.get('drill_for')
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    filtered_df = df.copy()
    
    if country:
        filtered_df = filtered_df[filtered_df['Country'] == country]
    if state:
        filtered_df = filtered_df[filtered_df['State/Province'] == state]
    if basin:
        filtered_df = filtered_df[filtered_df['Basin'] == basin]
    if drill_for:
        filtered_df = filtered_df[filtered_df['DrillFor'] == drill_for]
    if start_date:
        filtered_df = filtered_df[filtered_df['US_PublishDate'] >= pd.to_datetime(start_date)]
    if end_date:
        filtered_df = filtered_df[filtered_df['US_PublishDate'] <= pd.to_datetime(end_date)]
    
    # Group by date and the specified dimension
    agg = filtered_df.groupby(['US_PublishDate', group_by]).agg({
        'Rig Count Value': 'sum'
    }).reset_index()
    
    # Pivot for easier charting
    pivot = agg.pivot(index='US_PublishDate', columns=group_by, values='Rig Count Value').fillna(0)
    pivot = pivot.reset_index()
    pivot['US_PublishDate'] = pivot['US_PublishDate'].dt.strftime('%Y-%m-%d')
    
    # Convert to list of records
    records = pivot.to_dict(orient='records')
    
    return jsonify({
        "data": records,
        "group_by": group_by,
        "groups": list(pivot.columns[1:]),  # All columns except date
        "data_points": len(records)
    })

@app.route('/unique/<column>')
@require_api_key
def get_unique_values(column):
    """Get unique values for a specific column"""
    df = load_data()
    
    if df.empty:
        return jsonify({"error": "No data loaded"}), 404
    
    if column not in df.columns:
        return jsonify({"error": f"Column '{column}' not found", "available_columns": list(df.columns)}), 404
    
    unique_values = sorted(df[column].dropna().unique().tolist())
    
    # Convert any non-serializable types
    unique_values = [str(v) if isinstance(v, pd.Timestamp) else v for v in unique_values]
    
    return jsonify({
        "column": column,
        "unique_values": unique_values,
        "count": len(unique_values)
    })

@app.route('/reload', methods=['POST'])
@require_api_key
def reload_data():
    """Force reload of CSV data"""
    load_data(force_reload=True)
    return jsonify({
        "status": "reloaded",
        "rows_loaded": len(_df_cache),
        "timestamp": datetime.now().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found", "message": str(e)}), 404

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"error": "Unauthorized", "message": str(e)}), 401

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error", "message": str(e)}), 500

if __name__ == '__main__':
    # Load data on startup
    load_data()
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"\n🚀 Baker Hughes Weekly API running on http://localhost:{port}")
    print(f"📊 CSV Path: {CSV_FILE_PATH}")
    print(f"🔑 API Key Protection: {'Enabled' if API_KEY else 'Disabled'}\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)