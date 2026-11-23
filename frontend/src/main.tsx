import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { HealthProvider } from './services/HealthContext'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <HealthProvider>
        <App />
      </HealthProvider>
    </BrowserRouter>
  </StrictMode>,
)
