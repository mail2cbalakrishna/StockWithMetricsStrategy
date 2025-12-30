#!/bin/bash

# Quick progress check for continuous stock fetcher

echo ""
echo "================================================================================"
echo "📊 CONTINUOUS FETCHER PROGRESS CHECK"
echo "================================================================================"
echo ""

# Database summary
docker-compose exec backend python -c "
from app.models.database import SessionLocal, StockData
from sqlalchemy import func, distinct
from datetime import datetime, timedelta

db = SessionLocal()

# Total records
total_records = db.query(StockData).count()
unique_stocks = db.query(func.count(distinct(StockData.symbol))).scalar()

print(f'📈 Total Records: {total_records}')
print(f'🔢 Unique Stocks: {unique_stocks}')
print(f'🎯 Target: ~4,128 records (516 stocks × 8 years)')
print(f'📊 Completion: {(total_records/4128)*100:.1f}%')
print()

# Records by year
print('📅 RECORDS BY YEAR:')
year_data = db.query(
    StockData.year, 
    func.count(StockData.id).label('count')
).group_by(StockData.year).order_by(StockData.year.desc()).all()

for year, count in year_data:
    print(f'   {year}: {count:4d} stocks')
print()

# Latest 5 records
print('🆕 LATEST 5 RECORDS:')
latest = db.query(StockData).order_by(StockData.fetched_at.desc()).limit(5).all()
for stock in latest:
    fetch_time = stock.fetched_at.strftime('%Y-%m-%d %H:%M:%S')
    print(f'   {stock.symbol:6s} ({stock.year}) - {stock.data_source:10s} - {fetch_time}')
print()

# Records added in last hour
one_hour_ago = datetime.utcnow() - timedelta(hours=1)
recent_count = db.query(StockData).filter(StockData.fetched_at >= one_hour_ago).count()
print(f'⏱️  Records added in last hour: {recent_count}')

# Records added in last 24 hours
one_day_ago = datetime.utcnow() - timedelta(days=1)
day_count = db.query(StockData).filter(StockData.fetched_at >= one_day_ago).count()
print(f'📆 Records added in last 24 hours: {day_count}')

db.close()
"

echo ""
echo "================================================================================"
echo "📝 Recent Fetcher Activity (Last 10 fetches):"
echo "================================================================================"
docker-compose logs backend --tail=200 | grep -E "(Fetching|Stored|Updated)" | tail -10

echo ""
echo "================================================================================"
echo "✅ Progress check complete!"
echo "💡 Run this script anytime: ./check_progress.sh"
echo "================================================================================"
echo ""
