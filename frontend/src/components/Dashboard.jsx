import React, { useState, useEffect, useContext } from 'react'
import { useNavigate } from 'react-router-dom'
import { AuthContext } from '../context/AuthContext'
import apiService from '../services/api'
import {
  TrendingUp,
  Calendar,
  RefreshCw,
  LogOut,
  Menu,
  X,
  Database,
  Zap,
  Search,
  ChevronDown,
  Award,
  DollarSign,
  Percent
} from 'lucide-react'

function Dashboard() {
  const { keycloak } = useContext(AuthContext)
  const navigate = useNavigate()

  // State
  const [view, setView] = useState('yearly') // 'yearly' or 'monthly'
  const [selectedYear, setSelectedYear] = useState(2024) // Default to 2024 instead of current year
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1)
  const [limit, setLimit] = useState(10)
  const [stocks, setStocks] = useState([])
  const [loading, setLoading] = useState(false)
  const [cacheStats, setCacheStats] = useState(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const [selectedStock, setSelectedStock] = useState(null)
  const [error, setError] = useState(null)
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage] = useState(12) // Show 12 stocks per page

  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ]

  const years = Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - i)

  // Set API token
  useEffect(() => {
    if (keycloak?.token) {
      apiService.setToken(keycloak.token)
    }
  }, [keycloak])

  // Load cache stats
  useEffect(() => {
    loadCacheStats()
  }, [])

  // Load stocks when view changes
  useEffect(() => {
    loadStocks()
    setCurrentPage(1) // Reset to page 1 when filters change
  }, [view, selectedYear, selectedMonth, limit])

  const loadCacheStats = async () => {
    try {
      const stats = await apiService.getCacheStats()
      setCacheStats(stats)
    } catch (error) {
      console.error('Failed to load cache stats:', error)
    }
  }

  const loadStocks = async (forceRefresh = false) => {
    // Prevent multiple simultaneous requests
    if (loading && !forceRefresh) {
      console.log('⏳ Already loading stocks, skipping...')
      return
    }
    
    setLoading(true)
    setError(null)
    console.log(`📊 Loading stocks: ${view} view, year: ${selectedYear}, month: ${selectedMonth}, limit: ${limit}, force: ${forceRefresh}`)
    
    try {
      let data
      if (view === 'yearly') {
        data = await apiService.getStocksByYear(selectedYear, limit, forceRefresh)
      } else {
        data = await apiService.getStocksByMonth(selectedYear, selectedMonth, limit, forceRefresh)
      }
      console.log(`✅ Received ${data.stocks?.length || 0} stocks, cached: ${data.cached}`)
      setStocks(data.stocks || [])
      await loadCacheStats()
    } catch (error) {
      console.error('❌ Failed to load stocks:', error)
      // Better error message for 404 - data is still being calculated
      if (error.message.includes('Not Found') || error.message.includes('404')) {
        setError('processing')
      } else {
        setError(error.message)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    loadStocks(true)
  }

  const handleLogout = () => {
    keycloak?.logout()
    navigate('/login')
  }

  const handleWarmCache = async (year) => {
    try {
      await apiService.warmCache(year)
      alert(`Cache warming started for ${year}`)
      loadCacheStats()
    } catch (error) {
      alert('Failed to warm cache: ' + error.message)
    }
  }

  return (
    <div style={{ minHeight: '100vh', padding: '20px' }}>
      {/* Header */}
      <div className="glass" style={{
        padding: '20px 30px',
        borderRadius: '20px',
        marginBottom: '20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '15px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <TrendingUp size={32} color="white" />
          <div>
            <h1 style={{ color: 'white', fontSize: '24px', fontWeight: 'bold', margin: 0 }}>
              Magic Formula
            </h1>
            <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '14px', margin: 0 }}>
              Stock Analysis Dashboard
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {cacheStats && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 15px',
              background: 'rgba(255,255,255,0.1)',
              borderRadius: '10px'
            }}>
              <Database size={18} color="white" />
              <span style={{ color: 'white', fontSize: '14px' }}>
                {cacheStats.status === 'connected' ? '✓ Cache Ready' : '✗ Cache Down'}
              </span>
            </div>
          )}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            style={{
              background: 'rgba(255,255,255,0.2)',
              border: 'none',
              padding: '10px',
              borderRadius: '10px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center'
            }}
          >
            {menuOpen ? <X size={20} color="white" /> : <Menu size={20} color="white" />}
          </button>
          <button
            onClick={handleLogout}
            style={{
              background: 'rgba(255, 107, 107, 0.3)',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '10px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              color: 'white',
              fontWeight: 'bold'
            }}
          >
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </div>

      {/* Menu Panel */}
      {menuOpen && (
        <div className="glass fade-in" style={{
          padding: '20px',
          borderRadius: '20px',
          marginBottom: '20px'
        }}>
          <h3 style={{ color: 'white', marginBottom: '15px' }}>Quick Actions</h3>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button
              onClick={handleRefresh}
              disabled={loading}
              style={{
                background: 'rgba(102, 126, 234, 0.3)',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '10px',
                cursor: loading ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                color: 'white'
              }}
            >
              <RefreshCw size={18} className={loading ? 'spin' : ''} />
              Force Refresh
            </button>
            <button
              onClick={() => handleWarmCache(selectedYear)}
              style={{
                background: 'rgba(255, 193, 7, 0.3)',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '10px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                color: 'white'
              }}
            >
              <Zap size={18} />
              Warm Cache {selectedYear}
            </button>
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="glass" style={{
        padding: '25px',
        borderRadius: '20px',
        marginBottom: '20px'
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '15px'
        }}>
          {/* View Toggle */}
          <div>
            <label style={{ color: 'white', fontSize: '14px', display: 'block', marginBottom: '8px' }}>
              View Mode
            </label>
            <select
              value={view}
              onChange={(e) => setView(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '10px',
                border: '1px solid rgba(255,255,255,0.3)',
                background: 'rgba(255,255,255,0.1)',
                color: 'white',
                fontSize: '16px',
                cursor: 'pointer'
              }}
            >
              <option value="yearly">📅 Yearly View</option>
              <option value="monthly">📆 Monthly View</option>
            </select>
          </div>

          {/* Year Selector */}
          <div>
            <label style={{ color: 'white', fontSize: '14px', display: 'block', marginBottom: '8px' }}>
              Year
            </label>
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(parseInt(e.target.value))}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '10px',
                border: '1px solid rgba(255,255,255,0.3)',
                background: 'rgba(255,255,255,0.1)',
                color: 'white',
                fontSize: '16px',
                cursor: 'pointer'
              }}
            >
              {years.map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>

          {/* Month Selector (only for monthly view) */}
          {view === 'monthly' && (
            <div>
              <label style={{ color: 'white', fontSize: '14px', display: 'block', marginBottom: '8px' }}>
                Month
              </label>
              <select
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                style={{
                  width: '100%',
                  padding: '12px',
                  borderRadius: '10px',
                  border: '1px solid rgba(255,255,255,0.3)',
                  background: 'rgba(255,255,255,0.1)',
                  color: 'white',
                  fontSize: '16px',
                  cursor: 'pointer'
                }}
              >
                {months.map((month, index) => (
                  <option key={index} value={index + 1}>{month}</option>
                ))}
              </select>
            </div>
          )}

          {/* Limit Selector */}
          <div>
            <label style={{ color: 'white', fontSize: '14px', display: 'block', marginBottom: '8px' }}>
              Top Stocks
            </label>
            <select
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value))}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '10px',
                border: '1px solid rgba(255,255,255,0.3)',
                background: 'rgba(255,255,255,0.1)',
                color: 'white',
                fontSize: '16px',
                cursor: 'pointer'
              }}
            >
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
              <option value={15}>Top 15</option>
              <option value={20}>Top 20</option>
              <option value={30}>Top 30</option>
              <option value={50}>Top 50</option>
              <option value={100}>Top 100</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="glass" style={{
          padding: '20px',
          borderRadius: '15px',
          marginBottom: '20px',
          background: 'rgba(255, 107, 107, 0.2)',
          border: '1px solid rgba(255, 107, 107, 0.5)'
        }}>
          <p style={{ color: 'white', margin: 0 }}>⚠️ {error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="glass" style={{
          padding: '60px',
          borderRadius: '20px',
          textAlign: 'center'
        }}>
          <RefreshCw size={48} color="white" className="spin" style={{ margin: '0 auto 20px' }} />
          <p style={{ color: 'white', fontSize: '18px' }}>Loading stocks...</p>
        </div>
      )}

      {/* Stocks Grid */}
      {!loading && stocks.length > 0 && (
        <>
          {/* Pagination Info */}
          <div style={{ 
            color: 'rgba(255,255,255,0.8)', 
            fontSize: '14px', 
            marginBottom: '15px',
            textAlign: 'center'
          }}>
            Showing {Math.min((currentPage - 1) * itemsPerPage + 1, stocks.length)} - {Math.min(currentPage * itemsPerPage, stocks.length)} of {stocks.length} stocks
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
            gap: '20px'
          }}>
            {stocks.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage).map((stock, index) => (
              <div
                key={stock.symbol}
                className="glass fade-in"
                onClick={() => setSelectedStock(stock)}
                style={{
                  padding: '25px',
                  borderRadius: '20px',
                  cursor: 'pointer',
                transition: 'all 0.3s',
                position: 'relative',
                border: '2px solid transparent'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-5px)'
                e.currentTarget.style.borderColor = 'rgba(255,255,255,0.3)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)'
                e.currentTarget.style.borderColor = 'transparent'
              }}
            >
              {/* Rank Badge */}
              <div style={{
                position: 'absolute',
                top: '15px',
                right: '15px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 'bold',
                fontSize: '18px'
              }}>
                #{(currentPage - 1) * itemsPerPage + index + 1}
              </div>

              <div style={{ marginBottom: '15px' }}>
                <h3 style={{
                  color: 'white',
                  fontSize: '24px',
                  fontWeight: 'bold',
                  marginBottom: '5px'
                }}>
                  {stock.symbol}
                </h3>
                <p style={{
                  color: 'rgba(255,255,255,0.7)',
                  fontSize: '14px',
                  margin: 0
                }}>
                  {stock.name || 'N/A'}
                </p>
              </div>

              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '15px',
                marginTop: '20px'
              }}>
                <div>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px',
                    marginBottom: '5px'
                  }}>
                    <DollarSign size={16} color="rgba(255,255,255,0.7)" />
                    <span style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px' }}>
                      Earnings Yield
                    </span>
                  </div>
                  <p style={{
                    color: 'white',
                    fontSize: '18px',
                    fontWeight: 'bold',
                    margin: 0
                  }}>
                    {stock.earnings_yield ? `${(stock.earnings_yield * 100).toFixed(2)}%` : 'N/A'}
                  </p>
                </div>

                <div>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px',
                    marginBottom: '5px'
                  }}>
                    <Percent size={16} color="rgba(255,255,255,0.7)" />
                    <span style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px' }}>
                      ROC
                    </span>
                  </div>
                  <p style={{
                    color: 'white',
                    fontSize: '18px',
                    fontWeight: 'bold',
                    margin: 0
                  }}>
                    {stock.return_on_capital ? `${(stock.return_on_capital * 100).toFixed(2)}%` : 'N/A'}
                  </p>
                </div>
              </div>

              <div style={{
                marginTop: '15px',
                paddingTop: '15px',
                borderTop: '1px solid rgba(255,255,255,0.2)'
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px'
                }}>
                  <Award size={16} color="#FFD700" />
                  <span style={{ color: 'white', fontSize: '14px', fontWeight: 'bold' }}>
                    Score: {stock.combined_rank || 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Pagination Controls */}
        {stocks.length > itemsPerPage && (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '10px',
            marginTop: '30px',
            flexWrap: 'wrap'
          }}>
            {/* Previous Button */}
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              style={{
                padding: '12px 24px',
                borderRadius: '10px',
                border: 'none',
                background: currentPage === 1 ? 'rgba(255,255,255,0.1)' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                fontSize: '16px',
                fontWeight: 'bold',
                cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                opacity: currentPage === 1 ? 0.5 : 1,
                transition: 'all 0.3s'
              }}
            >
              Previous
            </button>

            {/* Page Numbers */}
            {Array.from({ length: Math.ceil(stocks.length / itemsPerPage) }, (_, i) => i + 1).map(pageNum => (
              <button
                key={pageNum}
                onClick={() => setCurrentPage(pageNum)}
                style={{
                  padding: '12px 18px',
                  borderRadius: '10px',
                  border: 'none',
                  background: currentPage === pageNum 
                    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' 
                    : 'rgba(255,255,255,0.1)',
                  color: 'white',
                  fontSize: '16px',
                  fontWeight: currentPage === pageNum ? 'bold' : 'normal',
                  cursor: 'pointer',
                  transition: 'all 0.3s',
                  minWidth: '45px'
                }}
                onMouseEnter={(e) => {
                  if (currentPage !== pageNum) {
                    e.currentTarget.style.background = 'rgba(255,255,255,0.2)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (currentPage !== pageNum) {
                    e.currentTarget.style.background = 'rgba(255,255,255,0.1)'
                  }
                }}
              >
                {pageNum}
              </button>
            ))}

            {/* Next Button */}
            <button
              onClick={() => setCurrentPage(prev => Math.min(Math.ceil(stocks.length / itemsPerPage), prev + 1))}
              disabled={currentPage === Math.ceil(stocks.length / itemsPerPage)}
              style={{
                padding: '12px 24px',
                borderRadius: '10px',
                border: 'none',
                background: currentPage === Math.ceil(stocks.length / itemsPerPage) 
                  ? 'rgba(255,255,255,0.1)' 
                  : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                fontSize: '16px',
                fontWeight: 'bold',
                cursor: currentPage === Math.ceil(stocks.length / itemsPerPage) ? 'not-allowed' : 'pointer',
                opacity: currentPage === Math.ceil(stocks.length / itemsPerPage) ? 0.5 : 1,
                transition: 'all 0.3s'
              }}
            >
              Next
            </button>
          </div>
        )}
      </>
      )}

      {/* No Data / Processing */}
      {!loading && stocks.length === 0 && (
        <div className="glass" style={{
          padding: '60px',
          borderRadius: '20px',
          textAlign: 'center'
        }}>
          {error === 'processing' ? (
            <>
              <div className="pulse" style={{ marginBottom: '20px' }}>
                <Database size={48} color="#4ade80" style={{ margin: '0 auto' }} />
              </div>
              <h3 style={{ color: '#4ade80', fontSize: '24px', fontWeight: 'bold', marginBottom: '10px' }}>
                🚀 Analyzing Market Data
              </h3>
              <p style={{ color: 'rgba(255,255,255,0.9)', fontSize: '16px', marginBottom: '20px' }}>
                Our intelligent system is fetching and analyzing ALL stocks from the market using the Magic Formula.
              </p>
              <div style={{
                background: 'rgba(74, 222, 128, 0.1)',
                border: '1px solid rgba(74, 222, 128, 0.3)',
                borderRadius: '10px',
                padding: '20px',
                marginTop: '20px'
              }}>
                <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '14px', margin: 0 }}>
                  📊 <strong>Analyzing:</strong> ALL stocks from NASDAQ + NYSE exchanges (8,000+ stocks)<br/>
                  ⏱️ <strong>First-time setup:</strong> Takes time to analyze entire market<br/>
                  ⚡ <strong>After completion:</strong> All responses will be instant (&lt;100ms)!<br/>
                  🔄 <strong>Refresh this page</strong> periodically to check progress
                </p>
              </div>
            </>
          ) : (
            <>
              <Search size={48} color="rgba(255,255,255,0.5)" style={{ margin: '0 auto 20px' }} />
              <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '18px' }}>
                No stocks found for this period
              </p>
            </>
          )}
        </div>
      )}

      {/* Detail Modal */}
      {selectedStock && (
        <div
          onClick={() => setSelectedStock(null)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
            zIndex: 1000
          }}
        >
          <div
            className="glass fade-in"
            onClick={(e) => e.stopPropagation()}
            style={{
              maxWidth: '600px',
              width: '100%',
              maxHeight: '80vh',
              overflow: 'auto',
              padding: '40px',
              borderRadius: '20px'
            }}
          >
            <button
              onClick={() => setSelectedStock(null)}
              style={{
                position: 'absolute',
                top: '20px',
                right: '20px',
                background: 'rgba(255,255,255,0.2)',
                border: 'none',
                borderRadius: '50%',
                width: '40px',
                height: '40px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer'
              }}
            >
              <X size={20} color="white" />
            </button>

            <h2 style={{ color: 'white', fontSize: '32px', marginBottom: '10px' }}>
              {selectedStock.symbol}
            </h2>
            <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '16px', marginBottom: '30px' }}>
              {selectedStock.name || 'Company Name Not Available'}
            </p>

            <div style={{
              display: 'grid',
              gap: '20px'
            }}>
              <DetailRow label="Earnings Yield" value={selectedStock.earnings_yield ? `${(selectedStock.earnings_yield * 100).toFixed(2)}%` : 'N/A'} />
              <DetailRow label="Return on Capital" value={selectedStock.return_on_capital ? `${(selectedStock.return_on_capital * 100).toFixed(2)}%` : 'N/A'} />
              <DetailRow label="Combined Rank" value={selectedStock.combined_rank || 'N/A'} />
              <DetailRow label="Market Cap" value={selectedStock.market_cap ? `$${(selectedStock.market_cap / 1e9).toFixed(2)}B` : 'N/A'} />
              <DetailRow label="Enterprise Value" value={selectedStock.enterprise_value ? `$${(selectedStock.enterprise_value / 1e9).toFixed(2)}B` : 'N/A'} />
              <DetailRow label="EBIT" value={selectedStock.ebit ? `$${(selectedStock.ebit / 1e9).toFixed(2)}B` : 'N/A'} />
            </div>

            <div style={{
              marginTop: '30px',
              padding: '20px',
              background: 'rgba(102, 126, 234, 0.2)',
              borderRadius: '15px'
            }}>
              <h4 style={{ color: 'white', marginBottom: '10px' }}>💡 Investment Insight</h4>
              <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '14px', lineHeight: '1.6', margin: 0 }}>
                This stock ranks in the top {limit} based on Magic Formula criteria, 
                combining high earnings yield and strong return on capital.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function DetailRow({ label, value }) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '15px',
      background: 'rgba(255,255,255,0.05)',
      borderRadius: '10px'
    }}>
      <span style={{ color: 'rgba(255,255,255,0.7)', fontSize: '14px' }}>{label}</span>
      <span style={{ color: 'white', fontSize: '18px', fontWeight: 'bold' }}>{value}</span>
    </div>
  )
}

export default Dashboard
