#!/bin/bash

echo ""
echo "================================================================================"
echo "⏱️  STARTING 1-HOUR MONITORING (Checking every minute for 60 minutes)"
echo "================================================================================"
echo ""

START_TIME=$(date +%s)
START_RECORDS=$(docker-compose exec -T backend python -c "
from app.models.database import SessionLocal, StockData
db = SessionLocal()
count = db.query(StockData).count()
db.close()
print(count)
" 2>/dev/null)

echo "📊 Starting Records: $START_RECORDS"
echo "🕐 Start Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "================================================================================"

# Monitor for 60 minutes (60 checks, 1 per minute)
for i in {1..60}; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    ELAPSED_MIN=$((ELAPSED / 60))
    
    # Get current record count
    CURRENT_RECORDS=$(docker-compose exec -T backend python -c "
from app.models.database import SessionLocal, StockData
from sqlalchemy import func, distinct
db = SessionLocal()
total = db.query(StockData).count()
unique = db.query(func.count(distinct(StockData.symbol))).scalar()
db.close()
print(f'{total},{unique}')
" 2>/dev/null)
    
    TOTAL=$(echo $CURRENT_RECORDS | cut -d',' -f1)
    UNIQUE=$(echo $CURRENT_RECORDS | cut -d',' -f2)
    NEW_RECORDS=$((TOTAL - START_RECORDS))
    RATE=$(echo "scale=1; $NEW_RECORDS / $ELAPSED_MIN" | bc 2>/dev/null)
    
    # Get latest 3 records
    LATEST=$(docker-compose exec -T backend python -c "
from app.models.database import SessionLocal, StockData
db = SessionLocal()
latest = db.query(StockData).order_by(StockData.fetched_at.desc()).limit(3).all()
for s in latest:
    print(f'{s.symbol}_{s.year}', end=' ')
db.close()
" 2>/dev/null)
    
    echo "[$i/60] $(date '+%H:%M:%S') | Records: $TOTAL (+$NEW_RECORDS) | Stocks: $UNIQUE | Rate: ${RATE}/min | Latest: $LATEST"
    
    # Every 10 minutes, show detailed summary
    if [ $((i % 10)) -eq 0 ]; then
        echo ""
        echo "────────────────────────────────────────────────────────────────────────────────"
        echo "📊 ${ELAPSED_MIN}-Minute Summary:"
        echo "   • Total Records: $TOTAL"
        echo "   • New Records: +$NEW_RECORDS"
        echo "   • Unique Stocks: $UNIQUE"
        echo "   • Avg Rate: ${RATE} records/minute"
        echo "   • Projected/Hour: $(echo "$RATE * 60" | bc) records"
        echo "────────────────────────────────────────────────────────────────────────────────"
        echo ""
    fi
    
    # Wait 60 seconds before next check (unless it's the last iteration)
    if [ $i -lt 60 ]; then
        sleep 60
    fi
done

# Final summary
FINAL_TIME=$(date +%s)
TOTAL_ELAPSED=$((FINAL_TIME - START_TIME))
TOTAL_MIN=$((TOTAL_ELAPSED / 60))

FINAL_RECORDS=$(docker-compose exec -T backend python -c "
from app.models.database import SessionLocal, StockData
from sqlalchemy import func, distinct
db = SessionLocal()
total = db.query(StockData).count()
unique = db.query(func.count(distinct(StockData.symbol))).scalar()
db.close()
print(f'{total},{unique}')
" 2>/dev/null)

FINAL_TOTAL=$(echo $FINAL_RECORDS | cut -d',' -f1)
FINAL_UNIQUE=$(echo $FINAL_RECORDS | cut -d',' -f2)
TOTAL_NEW=$((FINAL_TOTAL - START_RECORDS))
FINAL_RATE=$(echo "scale=2; $TOTAL_NEW / $TOTAL_MIN" | bc 2>/dev/null)

echo ""
echo "================================================================================"
echo "✅ 1-HOUR MONITORING COMPLETE"
echo "================================================================================"
echo ""
echo "📊 FINAL SUMMARY:"
echo "   • Start Records: $START_RECORDS"
echo "   • Final Records: $FINAL_TOTAL"
echo "   • New Records Added: +$TOTAL_NEW"
echo "   • Unique Stocks: $FINAL_UNIQUE"
echo "   • Time Elapsed: $TOTAL_MIN minutes"
echo "   • Average Rate: ${FINAL_RATE} records/minute"
echo "   • Projected Daily: $(echo "$FINAL_RATE * 60 * 24" | bc) records/day"
echo ""
echo "🎯 ESTIMATED COMPLETION:"
if [ $(echo "$FINAL_RATE > 0" | bc) -eq 1 ]; then
    REMAINING=$((4128 - FINAL_TOTAL))
    HOURS_LEFT=$(echo "scale=1; $REMAINING / ($FINAL_RATE * 60)" | bc)
    DAYS_LEFT=$(echo "scale=1; $HOURS_LEFT / 24" | bc)
    echo "   • Remaining Records: $REMAINING"
    echo "   • Estimated Hours: $HOURS_LEFT"
    echo "   • Estimated Days: $DAYS_LEFT"
fi
echo ""
echo "================================================================================"
