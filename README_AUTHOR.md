# Stock With Metrics Strategy - Magic Formula Stock Analysis

**Author:** Balakrishna C  
**License:** MIT License  
**Created:** 2025

---

## Project Overview

Stock With Metrics Strategy is a sophisticated **Magic Formula Stock Analysis platform** that applies the proven investment methodology to identify undervalued stocks with strong fundamentals. The system features a complete tech stack with React frontend, FastAPI backend, PostgreSQL database, Keycloak authentication, and AI-powered stock analysis.

### Key Features

- 🎯 **Magic Formula Analysis**: Ranks stocks by earnings yield and return on capital
- 📊 **10,488+ Stock Records**: Historical data from 2017-2024 across 1,753 stocks
- 🔐 **Keycloak OAuth2 Authentication**: Secure user authentication and role-based access
- 🚀 **Real-time Data Fetching**: Continuous fetcher for S&P 500, NASDAQ-100, and Dow 30
- 💾 **Multi-Database Support**: PostgreSQL for metrics, MongoDB for company info
- 🐳 **Docker Containerized**: Complete microservices architecture
- 📱 **Responsive UI**: React 18.2 + Vite frontend with dynamic hostname detection
- 🔄 **CI/CD Ready**: Full deployment pipeline with environment configuration

---

## Architecture

### Services

```
┌─────────────────────────────────────────────────────────┐
│         STOCK METRICS STRATEGY SYSTEM (2025)            │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Frontend (React 18.2 + Vite)         Port 3000          │
│  ├─ Dashboard Component                                  │
│  ├─ Login Component                                      │
│  └─ Dynamic Keycloak Integration                        │
│                                                           │
│  Backend (FastAPI)                    Port 8000          │
│  ├─ Magic Formula Service                               │
│  ├─ Stock Data Service                                  │
│  ├─ Continuous Fetcher                                  │
│  ├─ Multi-Source Data Fetcher                           │
│  └─ Keycloak Authentication                             │
│                                                           │
│  Authentication (Keycloak 23.0)       Port 8090          │
│  ├─ OAuth2/OpenID Connect                               │
│  ├─ User Management                                      │
│  └─ Realm: stock-analysis                               │
│                                                           │
│  Databases                                               │
│  ├─ PostgreSQL 15 (Port 5432)                           │
│  │  └─ stock_data: 10,488 records                       │
│  ├─ MongoDB 7 (Port 27018)                              │
│  │  └─ stock_analysis.stockinfo: 12,278 records         │
│  └─ Redis 7 (Port 6379)                                 │
│     └─ Caching & Session Storage                        │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Frontend | React | 18.2 |
| Build Tool | Vite | Latest |
| Backend | FastAPI | Latest |
| Auth | Keycloak | 23.0 |
| Database (Primary) | PostgreSQL | 15 |
| Database (Backup) | MongoDB | 7 |
| Cache | Redis | 7 |
| Orchestration | Docker Compose | Latest |

---

## Installation & Setup

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Machine IP: 192.168.1.207 (configurable in docker-compose.yml)

### Quick Start

```bash
# Clone repository
git clone <repo-url>
cd StockWithMetricsStrategy

# Build and start all services
docker-compose up -d --build

# Verify all services are running
docker-compose ps

# Wait 30 seconds for Keycloak to initialize
sleep 30

# Access the application
# Frontend: http://localhost:3000 or http://192.168.1.207:3000
# Backend: http://localhost:8000
# Keycloak: http://localhost:8090
```

### Default Credentials

- **Frontend User**: admin / admin123
- **Keycloak Admin**: admin / admin123 (access at http://localhost:8090/admin)

---

## Database Structure

### PostgreSQL - stock_data Table

```
Columns:
- id (PRIMARY KEY)
- symbol (VARCHAR 10) - Stock ticker
- company_name (VARCHAR 255) - Company name
- sector (VARCHAR 100) - Industry sector
- year (INTEGER) - Fiscal year
- month (INTEGER) - Fiscal month (nullable)
- ebit (DOUBLE) - Earnings Before Interest & Tax
- enterprise_value (DOUBLE) - Market cap + total debt
- tangible_capital (DOUBLE) - Equity - Intangible assets
- earnings_yield (DOUBLE) - (EBIT / Enterprise Value) * 100
- return_on_capital (DOUBLE) - (EBIT / Total Capital) * 100
- market_cap (DOUBLE) - Company market capitalization
- current_price (DOUBLE) - Last known stock price
- data_source (VARCHAR 50) - Data origin
- fetched_at (TIMESTAMP) - Fetch timestamp
- updated_at (TIMESTAMP) - Last update timestamp

Indexes:
- PRIMARY KEY on id
- UNIQUE CONSTRAINT on (symbol, year, month)
- Indexes on earnings_yield, return_on_capital, year, symbol
```

### Data Coverage

- **Total Records**: 10,488
- **Unique Stocks**: 1,753
- **Years Covered**: 2017-2024
- **Data Source**: MongoDB SEC filings + Continuous fetcher

---

## API Endpoints

### Authentication Required Endpoints

```
GET /api/stocks/top/year/{year}?top_n=10&force_refresh=false
  Description: Get top stocks by Magic Formula ranking for a specific year
  Parameters:
    - year: Fiscal year (2017-2024)
    - top_n: Number of results (default: 10)
    - force_refresh: Bypass cache and fetch fresh data

GET /api/admin/cache/stats
  Description: Cache statistics (admin only)

GET /api/stocks/{symbol}/{year}
  Description: Get detailed stock metrics for specific symbol and year
```

### Authentication Flow

1. User accesses http://localhost:3000
2. Frontend detects if user is authenticated
3. If not authenticated, redirects to Keycloak login
4. Keycloak authenticates user against realm
5. Returns JWT token to frontend
6. Frontend includes token in all API requests
7. Backend validates token and returns data

---

## Magic Formula Methodology

The system implements the proven Magic Formula investment strategy:

### Scoring Formula

**Earnings Yield = (EBIT / Enterprise Value) × 100**
- Higher is better
- Identifies stocks with good earnings relative to valuation

**Return on Capital = (EBIT / Invested Capital) × 100**
- Higher is better
- Measures how efficiently company uses capital

**Magic Formula Rank** = Combined rank of both metrics
- Stocks ranked 1-10 are top candidates
- Filters by minimum thresholds:
  - Earnings Yield ≥ 0%
  - ROC ≥ 0%
  - Market Cap ≥ $1B

### Data Sources

1. **SEC Filings** (via Polygon.io)
   - Income Statement (Revenue, EBIT, Net Income)
   - Balance Sheet (Assets, Liabilities, Equity)
   - Cash Flow Statement

2. **Real-Time Data** (via multiple sources)
   - Yahoo Finance
   - Alpha Vantage
   - Polygon API
   - Wikipedia tables (S&P 500, NASDAQ-100, Dow 30)

3. **Continuous Fetcher**
   - Runs 24/7 in background
   - Updates 1 stock per minute
   - Respects API rate limits
   - Maintains data freshness

---

## Project Structure

```
StockWithMetricsStrategy/
├── backend/                          # FastAPI application
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── core/
│   │   │   └── config.py            # Configuration
│   │   ├── models/
│   │   │   ├── database.py          # SQLAlchemy models
│   │   │   └── schemas.py           # Pydantic schemas
│   │   ├── routers/
│   │   │   ├── stocks.py            # Stock endpoints
│   │   │   └── admin.py             # Admin endpoints
│   │   └── services/
│   │       ├── dynamic_magic_formula.py
│   │       ├── continuous_fetcher.py
│   │       ├── multi_source_fetcher.py
│   │       ├── stock_data_service.py
│   │       ├── cache_service.py
│   │       ├── keycloak_auth.py
│   │       └── background_processor.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── stock_info_fetcher.py        # Stock info fetcher
│
├── frontend/                         # React + Vite
│   ├── src/
│   │   ├── App.jsx                  # Main component
│   │   ├── main.jsx                 # Entry point
│   │   ├── index.css                # Styles
│   │   ├── components/
│   │   │   ├── Dashboard.jsx        # Main dashboard
│   │   │   └── Login.jsx            # Login page
│   │   ├── context/
│   │   │   └── AuthContext.jsx      # Auth context
│   │   └── services/
│   │       └── api.js               # API client
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   └── public/
│       └── mobile-test.html         # Mobile testing page
│
├── keycloak/
│   └── realm-export.json            # Realm configuration
│
├── docker-compose.yml               # Container orchestration
├── docker-compose.stockfetcher.yml  # Stock fetcher setup
├── start.sh                         # Start script
├── stop.sh                          # Stop script
├── status.sh                        # Status check script
├── migrate_mongodb_to_postgres_proper.py  # Data migration
├── LICENSE                          # MIT License
├── README.md                        # This file
└── STOCK_METRICS_STRATEGY_DOCUMENTATION.md  # Detailed docs
```

---

## Getting Started Workflow

### 1. Initial Setup
```bash
docker-compose up -d --build
sleep 30
```

### 2. Access Dashboard
```
http://localhost:3000
Login: admin / admin123
```

### 3. Explore Data
- Select year 2024 (or 2017-2023)
- View top 10 stocks by Magic Formula
- Click on stocks to see detailed metrics

### 4. Check API Health
```bash
# Test backend is running
curl http://localhost:8000/docs

# Check Keycloak
curl http://localhost:8090/realms/stock-analysis

# Check database
docker exec stock-analysis-postgres psql -U keycloak -d keycloak -c "SELECT COUNT(*) FROM stock_data"
```

---

## Migration & Data Management

### Restore Data from MongoDB
```bash
python3 migrate_mongodb_to_postgres_proper.py
```

This script:
- Reads 12,278 MongoDB stockinfo documents
- Extracts SEC filing financial data
- Calculates Magic Formula metrics
- Inserts 10,488 records into PostgreSQL
- Handles conflicts and validates data

### Database Backup
```bash
# Backup PostgreSQL
docker exec stock-analysis-postgres pg_dump -U keycloak keycloak > backup.sql

# Restore PostgreSQL
docker exec -i stock-analysis-postgres psql -U keycloak keycloak < backup.sql
```

---

## Configuration

### Environment Variables

**docker-compose.yml:**
```yaml
VITE_API_URL: http://192.168.1.207:8000
VITE_KEYCLOAK_URL: http://192.168.1.207:8090
DATABASE_URL: postgresql://keycloak:keycloak_password@postgres:5432/keycloak
REDIS_HOST: redis
REDIS_PORT: 6379
```

### Machine IP Configuration

Update `docker-compose.yml` if your machine IP is different:
```yaml
environment:
  VITE_API_URL: http://YOUR_IP:8000
  VITE_KEYCLOAK_URL: http://YOUR_IP:8090
```

Find your IP:
```bash
ifconfig | grep -A 2 "inet " | grep -v 127.0.0.1
```

---

## Troubleshooting

### Services Won't Start
```bash
# Check logs
docker-compose logs backend
docker-compose logs keycloak
docker-compose logs frontend

# Restart services
docker-compose restart
```

### Login Issues
- Verify Keycloak is healthy: `docker-compose logs keycloak`
- Check redirect URIs in keycloak/realm-export.json
- Clear browser cookies and cache
- Try incognito mode

### No Data in Dashboard
- Verify PostgreSQL has records: `docker exec stock-analysis-postgres psql -U keycloak -d keycloak -c "SELECT COUNT(*) FROM stock_data"`
- Check continuous fetcher logs: `docker logs postgres-fetcher`
- Run migration script: `python3 migrate_mongodb_to_postgres_proper.py`

### API 404 Errors
- Ensure authentication token is present
- Verify year parameter (2017-2024)
- Check backend logs: `docker-compose logs backend`

---

## Performance Notes

- **Initial Load**: 30 seconds (services startup)
- **Dashboard Load**: 2-3 seconds (with 10,488 records)
- **API Response**: <500ms per query (with caching)
- **Data Refresh**: Every 60 seconds (continuous fetcher)
- **Memory Usage**: ~2GB total for all services

---

## Security Considerations

⚠️ **Development Mode Warning**
- Default credentials should be changed in production
- Keycloak running without HTTPS (set `KC_HTTP_ENABLED=true` for dev only)
- Database passwords are public in docker-compose (use .env files in production)
- Redis and MongoDB are publicly accessible

### Production Hardening

1. Change default credentials
2. Enable HTTPS for Keycloak
3. Use environment variables for secrets
4. Restrict network access
5. Enable database authentication
6. Use secrets management system

---

## Contributing

This is a personal project by Balakrishna C. For modifications:
1. Maintain the license header
2. Document changes in comments
3. Test thoroughly with full dataset
4. Update README if adding features

---

## License

**MIT License** - See LICENSE file for details

Copyright (c) 2025 Balakrishna C

This software is provided AS-IS for educational and personal use.

---

## Support & Documentation

- **Full Documentation**: See `STOCK_METRICS_STRATEGY_DOCUMENTATION.md`
- **Mobile Access**: See `MOBILE_ACCESS_GUIDE.md`
- **Keycloak Setup**: See `KEYCLOAK_MANUAL_FIX.md`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | Dec 29, 2025 | Complete data migration, fixed Keycloak auth |
| 1.5 | Dec 7, 2025 | Fixed query logic for NULL months, improved schema |
| 1.0 | Dec 1, 2025 | Initial release with basic functionality |

---

## Author

**Balakrishna C**
- Created: December 2025
- Stock Analysis Platform with Magic Formula
- Full-stack Development (Backend, Frontend, DevOps, Data Science)

---

**Last Updated**: December 29, 2025

For questions or issues, refer to the detailed documentation files included in the project.
