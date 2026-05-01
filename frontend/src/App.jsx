import { useState, useCallback } from 'react'
import Sidebar from './components/Sidebar.jsx'
import WeatherPanel from './components/WeatherPanel.jsx'
import PredictionsPanel from './components/PredictionsPanel.jsx'
import RecommendationsPanel from './components/RecommendationsPanel.jsx'
import IrrigationPanel from './components/IrrigationPanel.jsx'
import AlertsPanel from './components/AlertsPanel.jsx'
import ChatbotPanel from './components/ChatbotPanel.jsx'
import ScenarioPanel from './components/ScenarioPanel.jsx'

const TABS = [
  { id: 'weather',   icon: '🌤️',  label: { en: 'Weather',         hi: 'मौसम' } },
  { id: 'predict',   icon: '📊',  label: { en: 'Predictions',     hi: 'पूर्वानुमान' } },
  { id: 'scenario',  icon: '🔮',  label: { en: 'What-If',         hi: 'क्या-अगर' } },
  { id: 'recommend', icon: '🌱',  label: { en: 'Recommendations', hi: 'सलाह' } },
  { id: 'irrigate',  icon: '💧',  label: { en: 'Irrigation',      hi: 'सिंचाई' } },
  { id: 'alerts',    icon: '⚠️',  label: { en: 'Alerts',          hi: 'अलर्ट' } },
  { id: 'chatbot',   icon: '🤖',  label: { en: 'AI Chat',         hi: 'AI चैट' } },
]

export default function App() {
  const [tab, setTab]  = useState('weather')
  const [lang, setLang] = useState('en')
  const [params, setParams] = useState({
    city: 'Delhi',
    crop: 'wheat',
    soil_moisture: 50,
    soil_ph: 6.5,
    N: 80,   // Nitrogen  kg/ha
    P: 40,   // Phosphorus kg/ha
    K: 40,   // Potassium  kg/ha
  })
  const [trigger, setTrigger] = useState(0)

  const runAnalysis = useCallback(() => setTrigger(t => t + 1), [])

  return (
    <div className="app-shell">
      <Sidebar
        tabs={TABS} tab={tab} setTab={setTab}
        lang={lang} setLang={setLang}
        params={params} setParams={setParams}
        onAnalyse={runAnalysis}
      />
      <main className="main-content">
        {tab === 'weather'   && <WeatherPanel         params={params} lang={lang} trigger={trigger} />}
        {tab === 'predict'   && <PredictionsPanel     params={params} lang={lang} trigger={trigger} />}
        {tab === 'scenario'  && <ScenarioPanel        params={params} lang={lang} trigger={trigger} />}
        {tab === 'recommend' && <RecommendationsPanel params={params} lang={lang} trigger={trigger} />}
        {tab === 'irrigate'  && <IrrigationPanel      params={params} lang={lang} trigger={trigger} />}
        {tab === 'alerts'    && <AlertsPanel          params={params} lang={lang} trigger={trigger} />}
        {tab === 'chatbot'   && <ChatbotPanel lang={lang} />}
      </main>
    </div>
  )
}
