# Stock Info Fetcher - MongoDB Batch Script

## Purpose
This standalone script fetches complete raw API responses from Polygon.io for **ALL active US stocks (8,000+)** and stores them in MongoDB. This is separate from the PostgreSQL continuous fetcher.

## Key Features
- **ALL US Stocks**: Automatically fetches 8,000+ active stock symbols from Polygon API
- **Separate from main app**: Runs independently, can be deleted after completion
- **MongoDB storage**: Stores complete raw API responses
- **Rate limited**: 1 stock per minute to respect API limits
- **Different API key**: Uses VajOJ1XdN_Z1mpb3J2wws7pwn0qeKWNv to avoid conflicts

## Setup

### 1. Install MongoDB (if not already installed)
```bash
# macOS
brew install mongodb-community
brew services start mongodb-community

# Verify MongoDB is running
mongo --version
```

### 2. Install Python Dependencies
```bash
pip install -r stock_info_requirements.txt
```

### 3. Run the Script
```bash
cd /Users/krishnasonofgoddess/StockWithMetricsStrategy/backend
python stock_info_fetcher.py
```

## MongoDB Schema

**Database**: `stock_database`  
**Collection**: `stockinfo`

**Document Structure**:
```javascript
{
  "symbol": "AAPL",
  "year": 2023,
  "month": null,           // null for annual data
  "fetched_at": ISODate("2024-01-15T10:30:00Z"),
  "company_details": {     // Complete Polygon company details response
    "ticker": "AAPL",
    "name": "Apple Inc.",
    "market": "stocks",
    // ... full response
  },
  "financials": {          // Complete Polygon financials response
    "results": [
      {
        "fiscal_year": "2023",
        "fiscal_period": "FY",
        "financials": {
          "income_statement": { /* ... */ },
          "balance_sheet": { /* ... */ },
          "cash_flow_statement": { /* ... */ }
        }
      }
    ],
    // ... full response
  },
  "source": "polygon",
  "status": "success"      // or "failed"
}
```

## Monitoring Progress

### Check MongoDB Records
```bash
# Open MongoDB shell
mongosh

# Use database
use stock_database

# Count total documents
db.stockinfo.count()

# Check latest entries
db.stockinfo.find().sort({fetched_at: -1}).limit(5)

# Count by status
db.stockinfo.aggregate([
  {$group: {_id: "$status", count: {$sum: 1}}}
])

# Count by symbol
db.stockinfo.aggregate([
  {$group: {_id: "$symbol", count: {$sum: 1}}},
  {$sort: {count: -1}}
])
```

### Check Script Logs
```bash
# Live tail of logs
tail -f /tmp/stock_info_fetcher.log

# Count successful fetches
grep "Successfully fetched" /tmp/stock_info_fetcher.log | wc -l

# Count failed fetches
grep "Failed to fetch" /tmp/stock_info_fetcher.log | wc -l
```

## Expected Timeline

- **Total stocks**: 8,000+ (ALL active US stocks from Polygon)
- **Years per stock**: 8 (2017-2024)
- **Total fetches**: ~64,000+
- **Rate**: 1 fetch/minute = 60/hour = 1,440/day
- **Duration**: ~45 days (1.5 months, accounting for failures)

## Running Alongside PostgreSQL Fetcher

This script uses a **different Polygon API key** (VajOJ1XdN_Z1mpb3J2wws7pwn0qeKWNv) to avoid rate limit conflicts with the existing PostgreSQL continuous fetcher (which uses 8oQY_6TRJX6KnrVyhzkzqLPFd4Jck1Qw).

Both can run simultaneously:
- **PostgreSQL Fetcher**: Extracts specific metrics (EBIT, ROC, etc.) → PostgreSQL
- **MongoDB Fetcher**: Stores complete raw responses → MongoDB

## Cleanup After Completion

Once data collection is complete, you can:

1. **Export MongoDB data** (optional):
```bash
mongoexport --db=stock_database --collection=stockinfo --out=stockinfo_export.json
```

2. **Delete the script**:
```bash
rm /Users/krishnasonofgoddess/StockWithMetricsStrategy/backend/stock_info_fetcher.py
rm /Users/krishnasonofgoddess/StockWithMetricsStrategy/backend/stock_info_requirements.txt
rm /Users/krishnasonofgoddess/StockWithMetricsStrategy/backend/STOCK_INFO_FETCHER_README.md
```

3. **Keep or drop MongoDB collection**:
```bash
# Keep: The data is useful for analysis
# Drop: If you only needed it temporarily
mongosh
use stock_database
db.stockinfo.drop()
```

## Troubleshooting

### MongoDB Connection Failed
```bash
# Check if MongoDB is running
brew services list | grep mongodb

# Start MongoDB if stopped
brew services start mongodb-community
```

### API Rate Limit Errors
- The script already has 60-second delays between fetches
- Verify you're using the correct API key
- Check Polygon.io dashboard for rate limit status

### Script Stops Unexpectedly
- Check logs: `tail -f /tmp/stock_info_fetcher.log`
- Verify MongoDB is still running
- Script can be safely restarted - it will skip already-fetched data

## Background Execution

To run in background and keep it running even after logout:

```bash
# Using nohup
nohup python stock_info_fetcher.py > /tmp/stock_info_output.log 2>&1 &

# Check if running
ps aux | grep stock_info_fetcher

# Stop background process
pkill -f stock_info_fetcher
```

---

**Created**: Auto-generated for temporary batch data collection  
**Deletable**: Yes, this entire setup can be removed after completion  
**Purpose**: Archive complete raw API responses for potential future analysis
