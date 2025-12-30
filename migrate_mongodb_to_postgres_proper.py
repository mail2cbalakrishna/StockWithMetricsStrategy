#!/usr/bin/env python3
"""
Stock With Metrics Strategy - Data Migration Tool
Author: Balakrishna C
License: MIT
Copyright (c) 2025 Balakrishna C

Complete migration of all MongoDB documents to PostgreSQL
Extracts financial data from nested SEC filings in MongoDB
"""
import psycopg2
from pymongo import MongoClient
from datetime import datetime

def get_financial_value(financials, path_list):
    """Extract nested financial value from financials dict"""
    try:
        value = financials
        for key in path_list:
            value = value.get(key, {})
            if isinstance(value, dict) and 'value' in value:
                return float(value['value'])
        return None
    except:
        return None

# MongoDB connection
print("Connecting to MongoDB...")
mongo_client = MongoClient('mongodb://localhost:27018/')
mongo_db = mongo_client['stock_analysis']
mongo_collection = mongo_db['stockinfo']

# PostgreSQL connection
print("Connecting to PostgreSQL...")
postgres_conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='keycloak',
    user='keycloak',
    password='keycloak_password'
)
postgres_cursor = postgres_conn.cursor()

# Get count from MongoDB
mongo_count = mongo_collection.count_documents({})
print(f"📊 MongoDB has {mongo_count} documents to migrate")

# Fetch all documents from MongoDB
print("Fetching documents from MongoDB...")
documents = list(mongo_collection.find({}))
print(f"Fetched {len(documents)} documents\n")

# Insert into PostgreSQL
inserted = 0
failed = 0
skipped = 0

print("⏳ Starting migration...")
for i, doc in enumerate(documents):
    try:
        # Extract basic data
        symbol = doc.get('symbol', '').upper()
        year = doc.get('year')
        month = doc.get('month')
        
        # Extract company details
        company_details = doc.get('company_details', {})
        company_name = company_details.get('name', symbol)
        sector = company_details.get('sic_description', '')
        market_cap = float(company_details.get('market_cap', 0)) if company_details.get('market_cap') else 0
        
        # Extract financial data from SEC filings
        financial_data = doc.get('financial_data', {})
        financials = financial_data.get('financials', {})
        
        # Extract from income statement
        income_stmt = financials.get('income_statement', {})
        revenue = get_financial_value(income_stmt, ['revenues', 'value'])
        operating_income = get_financial_value(income_stmt, ['operating_income_loss', 'value'])
        net_income = get_financial_value(income_stmt, ['net_income_loss_attributable_to_parent', 'value'])
        
        # Extract from balance sheet
        balance_sheet = financials.get('balance_sheet', {})
        assets = get_financial_value(balance_sheet, ['assets', 'value'])
        liabilities = get_financial_value(balance_sheet, ['liabilities', 'value'])
        equity = get_financial_value(balance_sheet, ['equity_attributable_to_parent', 'value'])
        current_liabilities = get_financial_value(balance_sheet, ['current_liabilities', 'value'])
        current_assets = get_financial_value(balance_sheet, ['current_assets', 'value'])
        intangible_assets = get_financial_value(balance_sheet, ['intangible_assets', 'value'])
        
        # Calculate derived metrics for Magic Formula
        # EBIT = Operating Income or (Net Income + Interest Expense + Tax Expense)
        ebit = operating_income if operating_income else (net_income or 0)
        
        # Tangible Capital = Equity - Intangible Assets
        tangible_capital = (equity or 0) - (intangible_assets or 0) if equity else None
        
        # Enterprise Value = Market Cap + Debt (simplified: use liabilities as proxy)
        enterprise_value = market_cap + (liabilities or 0) if market_cap > 0 else None
        
        # Earnings Yield = EBIT / Enterprise Value
        earnings_yield = (ebit / enterprise_value * 100) if (ebit and enterprise_value and enterprise_value > 0) else None
        
        # Return on Capital = EBIT / (Equity + Debt) or EBIT / Assets
        total_capital = (equity or 0) + (liabilities or 0) if equity and liabilities else (assets or None)
        return_on_capital = (ebit / total_capital * 100) if (ebit and total_capital and total_capital > 0) else None
        
        # Skip if missing critical metrics for Magic Formula
        if not all([ebit, enterprise_value, tangible_capital, earnings_yield, return_on_capital]):
            skipped += 1
            if skipped <= 5:
                print(f"  ⏭️  Skipping {symbol} {year}: missing metrics")
            continue
        
        current_price = None
        data_source = 'mongodb_sec_filing'
        fetched_at = datetime.now()
        updated_at = datetime.now()
        
        # Insert into PostgreSQL
        postgres_cursor.execute("""
            INSERT INTO stock_data (
                symbol, company_name, sector, year, month,
                ebit, enterprise_value, tangible_capital, earnings_yield,
                return_on_capital, market_cap, current_price, data_source,
                fetched_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (symbol, year, month) DO UPDATE SET
                company_name = EXCLUDED.company_name,
                ebit = EXCLUDED.ebit,
                enterprise_value = EXCLUDED.enterprise_value,
                tangible_capital = EXCLUDED.tangible_capital,
                earnings_yield = EXCLUDED.earnings_yield,
                return_on_capital = EXCLUDED.return_on_capital,
                market_cap = EXCLUDED.market_cap,
                updated_at = EXCLUDED.updated_at
        """, (
            symbol, company_name, sector, year, month,
            float(ebit), float(enterprise_value), float(tangible_capital),
            float(earnings_yield), float(return_on_capital),
            float(market_cap), current_price, data_source, fetched_at, updated_at
        ))
        inserted += 1
        
        if (i + 1) % 1000 == 0:
            print(f"  ✅ Processed {i + 1}/{len(documents)} records... ({inserted} inserted)")
            postgres_conn.commit()
        
    except Exception as e:
        failed += 1
        if failed <= 5:
            print(f"  ❌ Failed {doc.get('symbol')} {doc.get('year')}: {str(e)[:80]}")

# Final commit
postgres_conn.commit()
postgres_cursor.close()
postgres_conn.close()

print(f"\n✅ Migration complete!")
print(f"  Inserted:  {inserted}")
print(f"  Failed:    {failed}")
print(f"  Skipped:   {skipped}")
print(f"  Total:     {inserted + failed + skipped}")

# Verify
postgres_conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='keycloak',
    user='keycloak',
    password='keycloak_password'
)
postgres_cursor = postgres_conn.cursor()
postgres_cursor.execute("SELECT COUNT(*) FROM stock_data")
count = postgres_cursor.fetchone()[0]
postgres_cursor.execute("SELECT symbol, year, COUNT(*) as months FROM stock_data GROUP BY symbol, year ORDER BY symbol, year LIMIT 20")
rows = postgres_cursor.fetchall()
postgres_cursor.execute("SELECT MIN(year), MAX(year), COUNT(DISTINCT symbol) FROM stock_data")
year_stats = postgres_cursor.fetchone()
postgres_cursor.close()
postgres_conn.close()

print(f"\n📊 PostgreSQL Migration Summary:")
print(f"  Total records: {count}")
print(f"  Year range: {year_stats[0]} - {year_stats[1]}")
print(f"  Unique symbols: {year_stats[2]}")
print(f"\nTop 20 records by symbol/year:")
for row in rows:
    print(f"  {row[0]:6} ({row[1]}): {row[2]:2} month(s)")
