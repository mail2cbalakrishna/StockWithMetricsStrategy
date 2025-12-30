#!/bin/bash

# Monitor MongoDB Stock Info Fetcher
# Shows real-time progress of the batch fetcher

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         MongoDB Stock Info Fetcher - Live Monitor           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if MongoDB is running
if ! pgrep -x "mongod" > /dev/null; then
    echo "❌ MongoDB is not running!"
    echo "   Start it with: brew services start mongodb-community"
    exit 1
fi

echo "✅ MongoDB is running"
echo ""

# MongoDB connection
MONGO_CMD="mongosh stock_analysis --quiet --eval"

# Get current counts
echo "📊 Current Statistics:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Total documents
TOTAL=$($MONGO_CMD "db.stockinfo.countDocuments({})")
echo "   Total Records: $TOTAL"

# Unique symbols
UNIQUE_SYMBOLS=$($MONGO_CMD "db.stockinfo.distinct('symbol').length")
echo "   Unique Symbols: $UNIQUE_SYMBOLS"

# Records by year
echo ""
echo "   Records by Year:"
$MONGO_CMD "
db.stockinfo.aggregate([
  {\$group: {_id: '\$year', count: {\$sum: 1}}},
  {\$sort: {_id: -1}}
]).forEach(function(doc) {
  print('      ' + doc._id + ': ' + doc.count + ' records');
})
" | grep -v "^$"

# Latest 5 entries
echo ""
echo "📥 Latest Entries:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
$MONGO_CMD "
db.stockinfo.find({}, {symbol: 1, year: 1, company_name: 1, fetched_at: 1, _id: 0})
  .sort({fetched_at: -1})
  .limit(5)
  .forEach(function(doc) {
    print('   ' + doc.symbol + ' (' + doc.year + ') - ' + doc.company_name + ' at ' + doc.fetched_at.toISOString());
  })
" | grep -v "^$"

# Top 10 stocks by record count
echo ""
echo "🏆 Top 10 Stocks (by records):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
$MONGO_CMD "
db.stockinfo.aggregate([
  {\$group: {_id: '\$symbol', count: {\$sum: 1}}},
  {\$sort: {count: -1}},
  {\$limit: 10}
]).forEach(function(doc) {
  print('   ' + doc._id + ': ' + doc.count + ' records');
})
" | grep -v "^$"

# Calculate progress
echo ""
echo "📈 Progress Estimation:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Estimate total (8000 symbols × 8 years = 64000)
ESTIMATED_TOTAL=64000
PERCENTAGE=$(echo "scale=2; ($TOTAL * 100) / $ESTIMATED_TOTAL" | bc)

echo "   Estimated Total: ~$ESTIMATED_TOTAL"
echo "   Current Progress: $TOTAL / $ESTIMATED_TOTAL ($PERCENTAGE%)"

# Calculate completion time if fetching at 1/minute
REMAINING=$((ESTIMATED_TOTAL - TOTAL))
DAYS_REMAINING=$(echo "scale=1; $REMAINING / 1440" | bc)

echo "   Remaining: ~$REMAINING fetches"
echo "   ETA: ~$DAYS_REMAINING days (at 1/minute)"

# Check if fetcher is running
echo ""
echo "🔍 Fetcher Process Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if pgrep -f "stock_info_fetcher.py" > /dev/null; then
    echo "   ✅ Fetcher is RUNNING"
    PID=$(pgrep -f "stock_info_fetcher.py")
    echo "   Process ID: $PID"
else
    echo "   ❌ Fetcher is NOT running"
    echo "   Start it with: python stock_info_fetcher.py"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Run this script periodically to monitor progress"
echo "   Example: watch -n 60 ./monitor_mongodb_fetcher.sh"
echo ""
