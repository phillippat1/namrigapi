# SharePoint CSV to RapidAPI 

**Monetize your SharePoint data by selling it as an API on RapidAPI marketplace**

## What This Does

This API connects to your SharePoint CSV file (updated every Friday) and exposes the data through clean REST endpoints that you can sell on RapidAPI. Customers can subscribe to different pricing tiers and access your data programmatically.

## Features

- ✅ Automatic SharePoint authentication via Azure AD
- ✅ Smart caching (6 hours) for performance and cost efficiency
- ✅ RapidAPI-compatible with proxy authentication
- ✅ Pagination, filtering, and sorting built-in
- ✅ Professional API documentation
- ✅ Ready for production deployment

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your SharePoint credentials (see SETUP_GUIDE.md for details).

### 3. Test Locally

```bash
uvicorn sharepoint_api:app --reload
```

Visit: http://localhost:8000

### 4. Deploy & Sell

See **SETUP_GUIDE.md** for complete deployment and RapidAPI setup instructions.

## API Endpoints

### `GET /data`
Retrieve data with optional filtering

**Parameters:**
- `limit` - Max rows to return (default: 100, max: 1000)
- `offset` - Rows to skip for pagination
- `columns` - Comma-separated column names
- `sort_by` - Column to sort by
- `sort_order` - 'asc' or 'desc'

**Example:**
```bash
GET /data?limit=50&columns=name,value&sort_by=date&sort_order=desc
```

### `GET /columns`
List all available columns and data types

### `GET /stats`
Dataset statistics (row count, columns, last update time)

### `GET /health`
Health check endpoint for monitoring

## Files

- `sharepoint_api.py` - Main FastAPI application
- `requirements.txt` - Python dependencies
- `Procfile` - Heroku deployment config
- `SETUP_GUIDE.md` - Complete setup instructions
- `.env.example` - Environment variables template

## Deployment Options

- **Heroku** (Recommended for beginners) - Free tier available
- **Railway** - Simple, modern hosting
- **AWS/GCP/Azure** - For enterprise scale

See SETUP_GUIDE.md for step-by-step deployment instructions.

## Revenue Potential

Example pricing tiers:
- **Basic**: $9.99/month (1,000 requests)
- **Pro**: $49.99/month (10,000 requests)  
- **Enterprise**: $199.99/month (unlimited)

With just 10 Pro subscribers = $499.90/month recurring revenue!

## Support

Questions? Check SETUP_GUIDE.md or open an issue.

## License

MIT License - feel free to modify and sell!
