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
      <div style={{marginBottom:16}}>
        <div style={{fontSize:11,color:'var(--text3)',fontWeight:600,textTransform:'uppercase',letterSpacing:'0.08em',marginBottom:8}}>{t.quick}</div>
        <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>
          {QUICK[lang].map(q => (
            <button key={q} onClick={() => send(q)}
              style={{padding:'6px 14px',background:'var(--bg3)',border:'1px solid var(--border)',borderRadius:20,fontSize:12,color:'var(--text2)',cursor:'pointer',transition:'all 0.2s'}}
              onMouseEnter={e=>e.target.style.borderColor='var(--accent)'}
              onMouseLeave={e=>e.target.style.borderColor='var(--border)'}
            >{q}</button>
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
                <div style={{width:30,height:30,borderRadius:'50%',background:'linear-gradient(135deg,var(--accent),var(--accent2))',display:'flex',alignItems:'center',justifyContent:'center',fontSize:14,flexShrink:0}}>🌾</div>
              )}
              <div className="msg-bubble">{m.text}</div>
            </div>
          ))}
          {loading && (
            <div className="msg bot">
              <div style={{width:30,height:30,borderRadius:'50%',background:'linear-gradient(135deg,var(--accent),var(--accent2))',display:'flex',alignItems:'center',justifyContent:'center',fontSize:14}}>🌾</div>
              <div className="msg-bubble" style={{display:'flex',gap:6,alignItems:'center'}}>
                <span className="spinner" style={{width:12,height:12,borderWidth:2}} />
                <span style={{color:'var(--text3)',fontSize:12}}>Thinking…</span>
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
