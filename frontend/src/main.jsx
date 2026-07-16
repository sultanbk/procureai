/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Renders React App into the root index.html element.
 * 
 * What it means:
 * Vite client compiler start point.
 * 
 * Importance in Project:
 * Critical. Boots up the frontend web interface.
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { ToastProvider } from './components/ui/ToastProvider.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ToastProvider>
      <App />
    </ToastProvider>
  </StrictMode>,
)
