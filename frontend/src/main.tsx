import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
// import App from './App.tsx'
import RecommendationPage from './pages/RecommendationPage.tsx'
// import PlayerPicker from './components/PlayerPicker.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RecommendationPage/>
    {/* <PlayerPicker/> */}
    {/* <App /> */}
  </StrictMode>,
)
