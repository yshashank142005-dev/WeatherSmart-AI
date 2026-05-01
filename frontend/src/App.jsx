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
  const activeTab = TABS.find(item => item.id === tab)

  const HELP_TEXT = {
    en: {
      title: 'Understand every feature quickly',
      sub: 'Use the quick guide below, then run analysis to refresh all modules with your latest farm inputs.',
      run: 'Run Analysis refreshes weather, predictions, recommendations, irrigation, alerts, and AI chat context.',
    },
    hi: {
      title: 'हर फीचर को आसानी से समझें',
      sub: 'नीचे दिए गए त्वरित गाइड से शुरू करें, फिर अपने इनपुट के साथ सभी मॉड्यूल अपडेट करने के लिए विश्लेषण चलाएँ।',
      run: 'विश्लेषण चलाने से मौसम, पूर्वानुमान, सलाह, सिंचाई, अलर्ट और AI चैट संदर्भ अपडेट होता है।',
    },
  }

  const FEATURE_HELP = {
    weather: {
      en: 'Current weather, 7-day forecast, and temperature trend in one place.',
      hi: 'वर्तमान मौसम, 7-दिन पूर्वानुमान और तापमान ट्रेंड एक साथ।',
    },
    predict: {
      en: 'ML-based yield score, confidence, and crop suitability ranking.',
      hi: 'ML आधारित उपज स्कोर, आत्मविश्वास और फसल उपयुक्तता रैंकिंग।',
    },
    scenario: {
      en: 'Test temperature/rainfall changes and compare yield impact instantly.',
      hi: 'तापमान/वर्षा बदलाव करके उपज प्रभाव तुरंत तुलना करें।',
    },
    recommend: {
      en: 'Actionable farm recommendations grouped by priority.',
      hi: 'प्राथमिकता के आधार पर स्पष्ट कृषि सलाह।',
    },
    irrigate: {
      en: 'Weekly irrigation plan with daily actions and water-saving tip.',
      hi: 'दैनिक कार्रवाई और जल-बचत सुझाव सहित साप्ताहिक सिंचाई योजना।',
    },
    alerts: {
      en: 'Extreme-weather alerts with notification dispatch options.',
      hi: 'अत्यधिक मौसम अलर्ट और नोटिफिकेशन भेजने के विकल्प।',
    },
    chatbot: {
      en: 'Ask questions in natural language with optional voice input.',
      hi: 'सामान्य भाषा में सवाल पूछें, आवाज इनपुट भी उपलब्ध।',
    },
  }

  const h = HELP_TEXT[lang]

  return (
    <div className="app-shell">
      <Sidebar
        tabs={TABS} tab={tab} setTab={setTab}
        lang={lang} setLang={setLang}
        params={params} setParams={setParams}
        onAnalyse={runAnalysis}
      />
      <main className="main-content">
        <section className="card mb-6 animate-fade-in">
          <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">{h.title}</h2>
              <p className="text-sm text-slate-300">{h.sub}</p>
            </div>
            <span className="inline-flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-xs font-semibold text-emerald-200">
              {activeTab?.icon} {activeTab?.label[lang]}
            </span>
          </div>
          <p className="mt-4 rounded-xl border border-indigo-400/20 bg-indigo-500/10 p-3 text-sm text-indigo-100">
            {h.run}
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {TABS.map(item => (
              <button
                key={`help-${item.id}`}
                onClick={() => setTab(item.id)}
                className={`rounded-xl border p-3 text-left transition-all duration-200 ${
                  tab === item.id
                    ? 'border-emerald-300/40 bg-emerald-500/15 shadow-lg shadow-emerald-500/10'
                    : 'border-white/10 bg-white/5 hover:-translate-y-0.5 hover:border-indigo-300/40 hover:bg-white/10'
                }`}
              >
                <div className="mb-1 text-sm font-semibold text-white">{item.icon} {item.label[lang]}</div>
                <div className="text-xs leading-relaxed text-slate-300">{FEATURE_HELP[item.id][lang]}</div>
              </button>
            ))}
          </div>
        </section>

        <div key={tab} className="animate-slide-up">
          {tab === 'weather'   && <WeatherPanel         params={params} lang={lang} trigger={trigger} />}
          {tab === 'predict'   && <PredictionsPanel     params={params} lang={lang} trigger={trigger} />}
          {tab === 'scenario'  && <ScenarioPanel        params={params} lang={lang} trigger={trigger} />}
          {tab === 'recommend' && <RecommendationsPanel params={params} lang={lang} trigger={trigger} />}
          {tab === 'irrigate'  && <IrrigationPanel      params={params} lang={lang} trigger={trigger} />}
          {tab === 'alerts'    && <AlertsPanel          params={params} lang={lang} trigger={trigger} />}
          {tab === 'chatbot'   && <ChatbotPanel lang={lang} />}
        </div>
      </main>
    </div>
  )
}
