import { useState, useRef, useEffect } from 'react'
import api from '../api'

const WELCOME = {
  en: "👋 Hello! I'm **WeatherSmart AI**. Ask me about crops, weather, irrigation, pests, or soil health. Type **help** to see all topics!",
  hi: "👋 नमस्ते! मैं **WeatherSmart AI** हूँ। फसल, मौसम, सिंचाई, कीट या मिट्टी के बारे में पूछें। सभी विषय देखने के लिए **help** टाइप करें!",
}

const QUICK = {
  en: ['💧 Irrigation tips', '🌾 Wheat advice', '🐛 Pest control', '🧪 Soil health', '📊 Yield info', 'help'],
  hi: ['💧 सिंचाई सुझाव', '🌾 गेहूँ सलाह', '🐛 कीट नियंत्रण', '🧪 मिट्टी स्वास्थ्य', '📊 उपज जानकारी', 'help'],
}

const T = {
  en: { title:'WeatherSmart AI', status:'Online', placeholder:'Ask about crops, weather, pests…', send:'Send', mic:'Voice Input', quick:'Quick Questions' },
  hi: { title:'WeatherSmart AI', status:'ऑनलाइन', placeholder:'फसल, मौसम, कीट के बारे में पूछें…', send:'भेजें', mic:'आवाज़ इनपुट', quick:'त्वरित प्रश्न' },
}

export default function ChatbotPanel({ lang }) {
  const [msgs, setMsgs]       = useState([{ role:'bot', text: WELCOME[lang] }])
  const [input, setInput]     = useState('')
  const [loading, setLoading] = useState(false)
  const [listening, setListening] = useState(false)
  const bottomRef = useRef(null)
  const t = T[lang]

  // update welcome when lang changes
  useEffect(() => {
    setMsgs([{ role:'bot', text: WELCOME[lang] }])
  }, [lang])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [msgs])

  const send = async (text) => {
    const msg = text || input.trim()
    if (!msg) return
    setInput('')
    setMsgs(m => [...m, { role:'user', text: msg }])
    setLoading(true)
    try {
      const r = await api.post('/api/chatbot', { message: msg, lang })
      setMsgs(m => [...m, { role:'bot', text: r.data.response }])
    } catch {
      setMsgs(m => [...m, { role:'bot', text:'⚠️ Connection error. Please ensure the backend is running.' }])
    }
    setLoading(false)
  }

  const startVoice = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) { alert('Voice input not supported in this browser.'); return }
    const rec = new SR()
    rec.lang = lang === 'hi' ? 'hi-IN' : 'en-IN'
    rec.onstart  = () => setListening(true)
    rec.onend    = () => setListening(false)
    rec.onresult = e => send(e.results[0][0].transcript)
    rec.start()
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">AI <span>Chatbot</span></h1>
        <p className="page-sub">Multilingual agricultural assistant with voice support</p>
      </div>

      {/* Quick questions */}
      <div className="mb-4">
        <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-400">{t.quick}</div>
        <div className="flex flex-wrap gap-2">
          {QUICK[lang].map(q => (
            <button
              key={q}
              onClick={() => send(q)}
              className="rounded-full border border-white/10 bg-slate-800/80 px-3 py-1.5 text-xs text-slate-300 transition hover:border-emerald-300/40 hover:text-emerald-200"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      <div className="chat-window">
        <div className="chat-header">
          <div className="chat-avatar">🌾</div>
          <div>
            <div className="chat-name">{t.title}</div>
            <div className="chat-status">● {t.status}</div>
          </div>
        </div>

        <div className="chat-messages">
          {msgs.map((m, i) => (
            <div className={`msg ${m.role}`} key={i}>
              {m.role === 'bot' && (
                <div className="flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-full bg-gradient-to-r from-emerald-400 to-indigo-500 text-sm">🌾</div>
              )}
              <div className="msg-bubble">{m.text}</div>
            </div>
          ))}
          {loading && (
            <div className="msg bot">
              <div className="flex h-[30px] w-[30px] items-center justify-center rounded-full bg-gradient-to-r from-emerald-400 to-indigo-500 text-sm">🌾</div>
              <div className="msg-bubble flex items-center gap-1.5">
                <span className="spinner h-3 w-3 border-[2px]" />
                <span className="text-xs text-slate-400">Thinking…</span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="chat-input-row">
          <button className={`chat-mic ${listening?'listening':''}`} onClick={startVoice} title={t.mic}>🎤</button>
          <input
            className="chat-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            placeholder={t.placeholder}
          />
          <button className="chat-send" onClick={() => send()}>➤</button>
        </div>
      </div>
    </div>
  )
}
