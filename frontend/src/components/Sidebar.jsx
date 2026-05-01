import { useState } from 'react'

const CROPS = [
  'wheat','rice','maize','cotton','sugarcane','soybean','barley',
  'chickpea','kidneybeans','pigeonpeas','mothbeans','mungbean','blackgram',
  'lentil','pomegranate','banana','mango','grapes','watermelon',
  'muskmelon','apple','orange','papaya','coconut','coffee',
]

const T = {
  en: {
    city:'City', crop:'Crop', moisture:'Soil Moisture', ph:'Soil pH',
    N:'Nitrogen (N)', P:'Phosphorus (P)', K:'Potassium (K)',
    analyse:'Run Analysis', language:'Language', nav:'Navigation', controls:'Controls',
  },
  hi: {
    city:'शहर', crop:'फसल', moisture:'मिट्टी नमी', ph:'मिट्टी pH',
    N:'नाइट्रोजन (N)', P:'फास्फोरस (P)', K:'पोटेशियम (K)',
    analyse:'विश्लेषण करें', language:'भाषा', nav:'नेविगेशन', controls:'नियंत्रण',
  },
}

export default function Sidebar({ tabs, tab, setTab, lang, setLang, params, setParams, onAnalyse }) {
  const t = T[lang]
  const [cityInput, setCityInput] = useState(params.city)
  const set = (k, v) => setParams(p => ({ ...p, [k]: v }))

  const commitCity = () => {
    const trimmed = cityInput.trim()
    if (trimmed) set('city', trimmed)
  }

  const handleAnalyse = () => {
    commitCity()
    onAnalyse()
  }

  return (
    <aside className="sidebar">
      <div className="logo">
        <span className="logo-icon">🌾</span>
        <div>
          <div className="logo-text">WeatherSmart</div>
          <div className="logo-sub">AI Agriculture Platform</div>
        </div>
      </div>

      <div className="nav-section">{t.nav}</div>
      {tabs.map(item => (
        <div
          key={item.id}
          className={`nav-item ${tab === item.id ? 'active' : ''}`}
          onClick={() => setTab(item.id)}
        >
          <span className="nav-icon">{item.icon}</span>
          {item.label[lang]}
        </div>
      ))}

      <div className="sidebar-controls">
        <div className="nav-section">{t.language}</div>
        <div className="lang-toggle">
          <button className={`lang-btn ${lang==='en'?'active':''}`} onClick={()=>setLang('en')}>EN</button>
          <button className={`lang-btn ${lang==='hi'?'active':''}`} onClick={()=>setLang('hi')}>हिंदी</button>
        </div>

        <div className="nav-section">{t.controls}</div>

        <div className="field-group">
          <label className="field-label">{t.city}</label>
          <input
            className="field-input"
            value={cityInput}
            onChange={e => setCityInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') { commitCity(); onAnalyse() } }}
            placeholder="e.g. Delhi"
          />
        </div>

        <div className="field-group">
          <label className="field-label">{t.crop}</label>
          <select className="field-select" value={params.crop} onChange={e=>set('crop',e.target.value)}>
            {CROPS.map(c=><option key={c} value={c}>{c.charAt(0).toUpperCase()+c.slice(1)}</option>)}
          </select>
        </div>

        <div className="field-group">
          <label className="field-label">{t.moisture}: <span className="text-accent">{params.soil_moisture}%</span></label>
          <div className="range-row">
            <input type="range" min="10" max="90" value={params.soil_moisture} onChange={e=>set('soil_moisture',+e.target.value)} />
          </div>
        </div>

        <div className="field-group">
          <label className="field-label">{t.ph}: <span className="text-accent">{params.soil_ph}</span></label>
          <div className="range-row">
            <input type="range" min="4" max="9" step="0.1" value={params.soil_ph} onChange={e=>set('soil_ph',+e.target.value)} />
          </div>
        </div>

        <div className="nav-section" style={{marginTop:12}}>🧪 Soil Nutrients (NPK)</div>

        <div className="field-group">
          <label className="field-label">{t.N}: <span className="text-accent">{params.N} kg/ha</span></label>
          <div className="range-row">
            <input type="range" min="0" max="140" value={params.N} onChange={e=>set('N',+e.target.value)} />
          </div>
        </div>

        <div className="field-group">
          <label className="field-label">{t.P}: <span className="text-accent">{params.P} kg/ha</span></label>
          <div className="range-row">
            <input type="range" min="5" max="145" value={params.P} onChange={e=>set('P',+e.target.value)} />
          </div>
        </div>

        <div className="field-group">
          <label className="field-label">{t.K}: <span className="text-accent">{params.K} kg/ha</span></label>
          <div className="range-row">
            <input type="range" min="5" max="205" value={params.K} onChange={e=>set('K',+e.target.value)} />
          </div>
        </div>

        <button className="btn-primary" onClick={handleAnalyse}>{t.analyse}</button>
      </div>
    </aside>
  )
}
