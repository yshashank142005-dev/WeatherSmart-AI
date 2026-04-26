import { useState, useEffect } from 'react'
import axios from 'axios'

const T = {
  en: { title:'Smart Recommendations', sub:'Hybrid rule-based + ML advisory', high:'High Priority', medium:'Medium Priority', low:'Low Priority', empty:'No recommendations. Run analysis first.' },
  hi: { title:'स्मार्ट सलाह', sub:'नियम-आधारित + ML सलाह', high:'उच्च प्राथमिकता', medium:'मध्यम प्राथमिकता', low:'कम प्राथमिकता', empty:'कोई सलाह नहीं। विश्लेषण करें।' },
}

export default function RecommendationsPanel({ params, lang, trigger }) {
  const [recs, setRecs] = useState([])
  const [loading, setLoading] = useState(false)
  const t = T[lang]

  useEffect(() => {
    const run = async () => {
      setLoading(true)
      try {
        const r = await axios.post('/api/recommend', {
          city: params.city, crop: params.crop,
          soil_moisture: params.soil_moisture, soil_ph: params.soil_ph,
        })
        setRecs(r.data.recommendations)
      } catch {}
      setLoading(false)
    }
    run()
  }, [params, trigger])

  const groups = ['high','medium','low']
  const labels = { high: t.high, medium: t.medium, low: t.low }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">{t.title}</h1>
        <p className="page-sub">{t.sub} — <span className="text-accent">{params.crop}</span> @ {params.city}</p>
      </div>

      {loading && <div className="loading-overlay"><span className="spinner"/> Generating recommendations…</div>}

      {!loading && recs.length === 0 && (
        <div className="loading-overlay" style={{color:'var(--text3)'}}>{t.empty}</div>
      )}

      {!loading && groups.map(priority => {
        const group = recs.filter(r => r.priority === priority)
        if (!group.length) return null
        return (
          <div className="card section-gap" key={priority}>
            <div className="card-title">
              <span>{priority==='high'?'🔴':priority==='medium'?'🟡':'🟢'}</span>
              {labels[priority]}
              <span className="badge" style={{marginLeft:'auto',background:'rgba(255,255,255,0.06)',color:'var(--text2)'}}>{group.length}</span>
            </div>
            <div className="rec-list">
              {group.map((r, i) => (
                <div className={`rec-item ${r.priority}`} key={i}>
                  <span className="rec-icon">{r.icon}</span>
                  <div className="rec-body">
                    <div className="rec-cat">{r.category}</div>
                    <div className="rec-msg">{r.message}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
