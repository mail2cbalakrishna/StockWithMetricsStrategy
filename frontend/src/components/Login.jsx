import React, { useContext, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AuthContext } from '../context/AuthContext'
import { TrendingUp, Sparkles, BarChart3 } from 'lucide-react'

function Login() {
  const { keycloak, authenticated } = useContext(AuthContext)
  const navigate = useNavigate()

  // If already authenticated, redirect to dashboard
  useEffect(() => {
    if (authenticated) {
      console.log('✅ Already authenticated, redirecting to dashboard')
      navigate('/dashboard')
    }
  }, [authenticated, navigate])

  const handleLogin = () => {
    console.log('🔐 Initiating Keycloak login...')
    // Keycloak login will redirect to Keycloak server
    // After successful login, user will be redirected back to app
    // The init() in App.jsx will detect authentication and update state
    keycloak?.login({
      redirectUri: window.location.origin + '/dashboard'
    }).catch(error => {
      console.error('❌ Login failed:', error)
    })
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div className="glass fade-in" style={{
        maxWidth: '500px',
        width: '100%',
        padding: '60px 40px',
        borderRadius: '30px',
        textAlign: 'center'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          marginBottom: '30px'
        }}>
          <div style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            padding: '20px',
            borderRadius: '20px',
            display: 'inline-flex'
          }}>
            <TrendingUp size={48} color="white" />
          </div>
        </div>

        <h1 style={{
          color: 'white',
          fontSize: '36px',
          fontWeight: 'bold',
          marginBottom: '10px'
        }}>
          Magic Formula
        </h1>
        <h2 style={{
          color: 'rgba(255,255,255,0.8)',
          fontSize: '18px',
          marginBottom: '40px'
        }}>
          Stock Analysis Platform
        </h2>

        <div style={{
          display: 'flex',
          justifyContent: 'space-around',
          marginBottom: '40px',
          padding: '0 20px'
        }}>
          <div>
            <Sparkles size={32} color="rgba(255,255,255,0.8)" />
            <p style={{ color: 'white', marginTop: '10px', fontSize: '14px' }}>Smart Analytics</p>
          </div>
          <div>
            <BarChart3 size={32} color="rgba(255,255,255,0.8)" />
            <p style={{ color: 'white', marginTop: '10px', fontSize: '14px' }}>Real-time Data</p>
          </div>
          <div>
            <TrendingUp size={32} color="rgba(255,255,255,0.8)" />
            <p style={{ color: 'white', marginTop: '10px', fontSize: '14px' }}>Top Rankings</p>
          </div>
        </div>

        <button
          onClick={handleLogin}
          className="glass"
          style={{
            width: '100%',
            padding: '18px',
            fontSize: '18px',
            fontWeight: 'bold',
            color: 'white',
            border: 'none',
            borderRadius: '15px',
            background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.6) 0%, rgba(118, 75, 162, 0.6) 100%)',
            cursor: 'pointer',
            transition: 'transform 0.2s',
          }}
          onMouseEnter={(e) => e.target.style.transform = 'scale(1.05)'}
          onMouseLeave={(e) => e.target.style.transform = 'scale(1)'}
        >
          Sign In with Keycloak
        </button>

        <p style={{
          color: 'rgba(255,255,255,0.6)',
          fontSize: '14px',
          marginTop: '20px'
        }}>
          Powered by Krishna using Magic Formula
        </p>
      </div>
    </div>
  )
}

export default Login
