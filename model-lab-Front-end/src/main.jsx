import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource-variable/dm-sans'
import './index.css'
import App from './App.jsx'
import { AnalysisProvider } from './context/AnalysisContext.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AnalysisProvider>
      <App />
    </AnalysisProvider>
  </StrictMode>,
)
