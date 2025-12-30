import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// StrictMode causes Keycloak double initialization - removed for production
ReactDOM.createRoot(document.getElementById('root')).render(<App />)
