# RapidAPI Setup Guide - Monetize Your SharePoint CSV Data

This guide will help you deploy and sell your API on RapidAPI marketplace.

## Overview

Your API pulls data from a SharePoint CSV file (updated every Friday) and exposes it through RapidAPI where customers can subscribe and pay for access.

---

## Step 1: Set Up SharePoint Access

### Register an Azure AD Application

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations** > **New registration**
3. Fill in:
   - **Name**: "RapidAPI Data Service"
   - **Supported account types**: "Accounts in this organizational directory only"
   - Click **Register**

4. Note down:
   - **Application (client) ID** - This is your `CLIENT_ID`
   - **Directory (tenant) ID** - This is your `TENANT_ID`

5. Create a client secret:
   - Go to **Certificates & secrets**
   - Click **New client secret**
   - Add description: "RapidAPI Secret"
   - Choose expiration (recommend 24 months)
   - Copy the **Value** - This is your `CLIENT_SECRET` (save it now, won't show again)

6. Grant SharePoint permissions:
   - Go to **API permissions**
   - Click **Add a permission** > **Microsoft Graph** > **Application permissions**
   - Add: `Sites.Read.All` and `Files.Read.All`
   - Click **Grant admin consent** (requires admin access)

### Get SharePoint Site ID

Run this PowerShell command (replace with your actual site URL):

```powershell
# Install module if needed
Install-Module -Name PnP.PowerShell

# Connect to SharePoint
Connect-PnPOnline -Url "https://yourcompany.sharepoint.com/sites/yoursite" -Interactive

# Get Site ID
Get-PnPSite | Select Id
```

Or use Microsoft Graph Explorer:
- Visit: https://developer.microsoft.com/en-us/graph/graph-explorer
- Sign in
- Run: `GET https://graph.microsoft.com/v1.0/sites/{hostname}:{site-path}`
- Example: `GET https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com:/sites/marketing`

---

## Step 2: Deploy Your API

### Option A: Deploy to Heroku (Easiest)

1. **Install Heroku CLI**: https://devcenter.heroku.com/articles/heroku-cli

2. **Create Heroku app**:
```bash
heroku create your-api-name
```

3. **Set environment variables**:
```bash
heroku config:set SHAREPOINT_CLIENT_ID="your-client-id"
heroku config:set SHAREPOINT_CLIENT_SECRET="your-client-secret"
heroku config:set SHAREPOINT_TENANT_ID="your-tenant-id"
heroku config:set SHAREPOINT_SITE_ID="your-site-id"
heroku config:set SHAREPOINT_FILE_PATH="/sites/YourSite/Shared Documents/yourfile.csv"
```

4. **Create Procfile**:
```bash
echo "web: uvicorn sharepoint_api:app --host 0.0.0.0 --port \$PORT" > Procfile
```

5. **Deploy**:
```bash
git init
git add .
git commit -m "Initial commit"
git push heroku main
```

### Option B: Deploy to Railway (Alternative)

1. Go to [Railway.app](https://railway.app)
2. Click **New Project** > **Deploy from GitHub**
3. Connect your repository
4. Add environment variables in Railway dashboard
5. Deploy automatically handles everything

### Option C: Deploy to AWS/GCP/Azure

- Use containerization (Docker) or serverless (Lambda/Functions)
- Set up environment variables in your cloud provider
- Ensure HTTPS endpoint is accessible

---

## Step 3: List on RapidAPI

### Create Provider Account

1. Go to [RapidAPI Provider Hub](https://rapidapi.com/provider)
2. Sign up as a provider
3. Complete your profile and payment information

### Add Your API

1. **Click "Add New API"**
2. **Fill in basic information**:
   - **API Name**: Give it a marketable name (e.g., "Weekly Industry Data API")
   - **Category**: Choose relevant category
   - **Description**: Describe what data you provide and how often it updates
   - **Tags**: Add relevant tags for discoverability

3. **Configure API Settings**:
   - **Base URL**: Your deployed API URL (e.g., `https://your-api-name.herokuapp.com`)
   - **Protocol**: HTTPS
   - **API Type**: REST

4. **Set Up Endpoints**:
   RapidAPI will auto-detect your endpoints from the base URL. Main endpoints:
   - `GET /data` - Main data endpoint
   - `GET /columns` - List available columns
   - `GET /stats` - Dataset statistics
   - `GET /health` - Health check

5. **Configure Authentication** (Optional):
   - Go to your deployed API environment variables
   - Set `RAPIDAPI_PROXY_SECRET` to a random secure string
   - Save this in RapidAPI dashboard under "Headers"

### Set Up Pricing Plans

1. **Go to "Plans" tab**
2. **Create pricing tiers** (examples):

   **Basic Plan** - $9.99/month
   - 1,000 requests/month
   - Rate limit: 10 requests/minute
   - Access to /data endpoint (100 rows max per request)

   **Pro Plan** - $49.99/month
   - 10,000 requests/month
   - Rate limit: 60 requests/minute
   - Access to all endpoints
   - Up to 1,000 rows per request

   **Enterprise Plan** - $199.99/month
   - Unlimited requests
   - Rate limit: 300 requests/minute
   - Priority support
   - Full dataset access

3. **Set quotas** for each plan using RapidAPI's quota system

---

## Step 4: Test Your API

### Test Directly

```bash
curl "https://your-api-name.herokuapp.com/data?limit=5"
```

### Test Through RapidAPI

1. Go to your API page on RapidAPI
2. Click "Test Endpoint"
3. Try different parameters:
   - `limit=10&offset=0`
   - `columns=column1,column2`
   - `sort_by=date&sort_order=desc`

---

## Step 5: Market Your API

### Optimize Your Listing

1. **Write compelling description**:
   - What data you provide
   - How often it updates (every Friday)
   - Use cases
   - Data quality and sources

2. **Add code examples** for popular languages:
   - Python
   - JavaScript
   - cURL
   - PHP

3. **Create documentation**:
   - Explain each endpoint
   - Show example responses
   - List all available parameters

### Promote Your API

- Share on LinkedIn, Twitter with #API hashtags
- Post in relevant Reddit communities (r/datasets, r/dataisbeautiful)
- Write blog posts about your data
- Create sample projects using your API
- Join API marketplaces besides RapidAPI

---

## Monitoring & Maintenance

### Track Usage

- RapidAPI dashboard shows:
  - Number of subscribers
  - Request volume
  - Revenue
  - Error rates

### Monitor Your Server

```bash
# Check Heroku logs
heroku logs --tail

# Monitor memory usage
heroku ps

# Check API health
curl "https://your-api-name.herokuapp.com/health"
```

### Update Data

Your SharePoint CSV updates every Friday automatically. The API caches for 6 hours, so customers see fresh data throughout the week.

---

## Environment Variables Summary

```bash
SHAREPOINT_CLIENT_ID=<your-azure-app-client-id>
SHAREPOINT_CLIENT_SECRET=<your-azure-app-secret>
SHAREPOINT_TENANT_ID=<your-azure-tenant-id>
SHAREPOINT_SITE_ID=<your-sharepoint-site-id>
SHAREPOINT_FILE_PATH=/sites/YourSite/Shared Documents/data.csv
RAPIDAPI_PROXY_SECRET=<random-secure-string> # Optional but recommended
```

---

## Troubleshooting

### "Could not acquire token" Error
- Verify CLIENT_ID, CLIENT_SECRET, and TENANT_ID are correct
- Ensure app has Sites.Read.All permission with admin consent

### "Error fetching data" Error
- Check SITE_ID is correct
- Verify FILE_PATH points to actual CSV file
- Ensure file is accessible by the app

### RapidAPI not connecting
- Verify base URL is correct and accessible publicly
- Check HTTPS is enabled
- Test endpoints directly first

### No subscribers
- Improve description and documentation
- Lower initial pricing to attract users
- Add code examples
- Promote on social media

---

## Next Steps

1. Set up SharePoint app registration
2. Deploy to hosting platform
3. Test all endpoints
4. List on RapidAPI
5. Set competitive pricing
6. Market your API
7. Monitor and iterate based on user feedback

Good luck with your API business! 🚀
