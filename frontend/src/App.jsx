/**
 * Stock With Metrics Strategy - React Frontend
 * Author: Balakrishna C
 * License: MIT
 * Copyright (c) 2025 Balakrishna C
 * 
 * Main application component with Keycloak authentication
 */
import React, { useState, useEffect, useRef } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Keycloak from 'keycloak-js'
import Dashboard from './components/Dashboard'
import Login from './components/Login'
import { AuthContext } from './context/AuthContext'

// Singleton Keycloak instance to prevent re-initialization
let keycloakSingleton = null
const getKeycloak = () => {
  if (!keycloakSingleton) {
    // Determine Keycloak URL based on context:
    // - Browser accessing from localhost/127.0.0.1 → use localhost:8090
    // - Browser accessing from IP (192.168.1.201) → use that IP:8090
    // - Fallback to environment variable if set
    const keycloakUrl = (() => {
      const hostname = window.location.hostname
      const protocol = window.location.protocol
      
      console.log(`📍 Browser hostname detected: ${hostname}`)
      
      // If on localhost/127.0.0.1/0.0.0.0, use localhost
      if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '0.0.0.0') {
        return `${protocol}//localhost:8090`
      }
      // If on any other hostname/IP, use that IP but map to port 8090
      const url = import.meta.env.VITE_KEYCLOAK_URL || `${protocol}//${hostname}:8090`
      return url
    })()
    
    console.log(`🔐 Keycloak URL resolved to: ${keycloakUrl}`)
    keycloakSingleton = new Keycloak({
      url: keycloakUrl,
      realm: 'stock-analysis',
      clientId: 'stock-analysis-client',
    })
  }
  return keycloakSingleton
}

function App() {
  const [authenticated, setAuthenticated] = useState(false)
  const [keycloak, setKeycloak] = useState(null)
  const [loading, setLoading] = useState(true)
  const initRef = useRef(false)

  useEffect(() => {
    // Prevent double initialization
    if (initRef.current) return
    initRef.current = true

    const kc = getKeycloak()
    console.log('🚀 Starting Keycloak initialization...')
    
    const timeout = setTimeout(() => {
      console.warn('⏱️ Keycloak timeout - proceeding without auth')
      setKeycloak(kc)
      setLoading(false)
    }, 5000)

    kc.init({
      onLoad: 'check-sso',
      checkLoginIframe: false,
      pkceMethod: 'S256', // Use PKCE for security
    }).then(authenticated => {
      clearTimeout(timeout)
      console.log('✅ Keycloak initialized, authenticated:', authenticated)
      setAuthenticated(authenticated)
      setKeycloak(kc)
      setLoading(false)

      // Set up token refresh
      if (authenticated) {
        console.log('🔐 User authenticated, token will auto-refresh')
        // Refresh token every 5 minutes
        setInterval(() => {
          kc.updateToken(70).then((refreshed) => {
            if (refreshed) {
              console.log('🔄 Token refreshed')
            }
          }).catch(() => {
            console.error('❌ Failed to refresh token')
            setAuthenticated(false)
          })
        }, 300000) // 5 minutes
      }
    }).catch(error => {
      clearTimeout(timeout)
      console.error('❌ Keycloak init failed:', error)
      setKeycloak(kc)
      setLoading(false)
    })

    return () => clearTimeout(timeout)
  }, [])

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        color: 'white',
        fontSize: '24px',
        gap: '20px'
      }}>
        <div className="pulse" style={{ fontSize: '48px' }}>⏳</div>
        <div>Initializing Magic Formula...</div>
        <div style={{ fontSize: '14px', opacity: 0.7 }}>
          Connecting to authentication service...
        </div>
        <div style={{ fontSize: '12px', opacity: 0.5, marginTop: '20px' }}>
          If this takes more than 5 seconds, check browser console (F12)
        </div>
      </div>
    )
  }

  return (
    <AuthContext.Provider value={{ keycloak, authenticated }}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/dashboard"
            element={authenticated ? <Dashboard /> : <Navigate to="/login" />}
          />
          <Route
            path="/"
            element={authenticated ? <Navigate to="/dashboard" /> : <Navigate to="/login" />}
          />
        </Routes>
      </BrowserRouter>
    </AuthContext.Provider>
  )
}

export default App
