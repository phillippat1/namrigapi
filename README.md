# Sell Your Data API on RapidAPI

**Turn Your Data Into Recurring Revenue**

Simple REST API powered by Supabase that you can sell on RapidAPI marketplace.

---

## What This Is

A production-ready API that:
- ✅ Connects to your Supabase database
- ✅ Exposes clean REST endpoints
- ✅ Works perfectly with RapidAPI
- ✅ Includes pagination, filtering, sorting, search
- ✅ Ready to deploy in minutes
- ✅ Ready to monetize immediately

## The Simple Flow

```
Your Data → Supabase → This API → RapidAPI → 💰
```

## Quick Start

### 1. Set Up Database (20 min)
1. Create Supabase account: https://supabase.com
2. Create new project
3. Upload your CSV data (drag & drop!)
4. Copy your API credentials

### 2. Deploy API (15 min)
1. Upload these files to GitHub
2. Connect Railway to your repo: https://railway.app
3. Add environment variables (Supabase credentials)
4. Deploy! (automatic)

### 3. List on RapidAPI (30 min)
1. Create provider account: https://rapidapi.com/provider
2. Add your API
3. Set up pricing tiers
4. Submit for review
5. Start earning! 💵

**Read `QUICKSTART_GUIDE.md` for detailed step-by-step instructions.**

---

## What's Included

### Main API (`api.py`)
Production-ready FastAPI application with:
- `/data` - Get data with filtering and pagination
- `/columns` - List available columns
- `/stats` - Dataset statistics  
- `/search` - Search within columns
- `/health` - Health check

### Helper Script (`update_data.py`)
Simple script to update your Supabase data:
```bash
python update_data.py
```

### Deployment Files
- `requirements.txt` - Python dependencies
- `Procfile` - Railway/Heroku config
- `.env.example` - Configuration template

### Documentation
- `QUICKSTART_GUIDE.md` - Complete setup guide (READ THIS FIRST!)
- `README.md` - This file

---

## API Endpoints

### GET /data
Retrieve data with optional filtering

**Example:**
```bash
GET /data?limit=10&sort_by=date&sort_order=desc
```

**Parameters:**
- `limit` - Max rows (1-1000, default: 100)
- `offset` - Skip rows (pagination)
- `columns` - Specific columns to return
- `sort_by` - Column to sort by
- `sort_order` - 'asc' or 'desc'

**Response:**
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "total_rows": 1000,
    "returned_rows": 10,
    "has_more": true
  }
}
```

### GET /search
Search within specific column

**Example:**
```bash
GET /search?query=texas&column=state&limit=50
```

### GET /columns
List all available columns

### GET /stats
Dataset statistics

---

## Environment Variables

Create a `.env` file:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
RAPIDAPI_PROXY_SECRET=make-up-random-string
```

---

## Pricing Strategy

Recommended tiers for RapidAPI:

**FREE** - $0/month
- 100 requests/month
- Gets people to try it

**BASIC** - $9.99/month
- 1,000 requests/month
- Casual users

**PRO** - $29.99/month ⭐
- 10,000 requests/month
- Most popular tier

**BUSINESS** - $99.99/month
- 100,000 requests/month
- Serious customers

**ENTERPRISE** - Custom
- Unlimited everything
- White-glove service

---

## Revenue Potential

**Conservative estimates:**

- Month 1: 5 subscribers = $50
- Month 3: 30 subscribers = $600/month
- Month 6: 100 subscribers = $2,700/month
- **Year 1: $20,000-40,000 total revenue**

With good marketing, many people 3-5x these numbers!

---

## Deployment Options

### Railway (Recommended)
- Easiest setup
- Free tier: 500 hours/month
- Auto-deploy from GitHub
- Generate domain with 1 click

### Heroku
- Reliable platform
- Free tier available
- Simple CLI

### Others
- Render.com
- Fly.io
- Any platform that supports Python

---

## Update Your Data

When you have new data:

**Option 1 - Manual (2 minutes):**
1. Go to Supabase Table Editor
2. Truncate table
3. Import new CSV
4. Done!

**Option 2 - Script (30 seconds):**
```bash
# Put your new data in data.csv
python update_data.py
```

---

## Tech Stack

- **Database**: Supabase (PostgreSQL)
- **API**: FastAPI (Python)
- **Hosting**: Railway / Heroku
- **Marketplace**: RapidAPI

---

## Files

```
├── api.py                 # Main API (FastAPI)
├── update_data.py         # Data update script
├── requirements.txt       # Python packages
├── Procfile              # Deployment config
├── .env.example          # Config template
├── QUICKSTART_GUIDE.md   # Detailed setup guide
└── README.md             # This file
```

---

## Support

- **Supabase Docs**: https://supabase.com/docs
- **Railway Docs**: https://docs.railway.app
- **RapidAPI Guide**: https://docs.rapidapi.com/docs/provider-quick-start-guide
- **FastAPI Docs**: https://fastapi.tiangolo.com

---

## Next Steps

1. **Read** `QUICKSTART_GUIDE.md` - Complete walkthrough
2. **Set up** Supabase - Import your data
3. **Deploy** to Railway - 1-click deploy
4. **List** on RapidAPI - Start selling!

---

## License

MIT - Use it, modify it, sell it!

---

**Ready to make money from your data? Read the Quick Start Guide and let's go! 🚀**
