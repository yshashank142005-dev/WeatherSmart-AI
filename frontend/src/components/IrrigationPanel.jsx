import { useState, useEffect } from 'react'
import api from '../api'

const T = {
  en: { title:'Irrigation Scheduler', sub:'Smart weekly water plan based on forecast & soil', need:'Weekly Water Need', rain:'Forecast Rainfall', net:'Net Irrigation Need', sessions:'Sessions/Week', tip:'Water Saving Tip', plan:'Daily Plan', empty:'Run analysis to generate irrigation schedule.' },
  hi: { title:'सिंचाई अनुसूची', sub:'पूर्वानुमान और मिट्टी पर आधारित साप्ताहिक योजना', need:'साप्ताहिक जल आवश्यकता', rain:'पूर्वानुमान वर्षा', net:'शुद्ध सिंचाई आवश्यकता', sessions:'सत्र/सप्ताह', tip:'जल बचत सुझाव', plan:'दैनिक योजना', empty:'सिंचाई योजना के लिए विश्लेषण करें।' },
}

export default function IrrigationPanel({ params, lang, trigger }) {
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(false)
  const t = T[lang]

  useEffect(() => {
    const run = async () => {
      setLoading(true)
      try {
        const r = await api.post('/api/irrigation', {
          city: params.city, crop: params.crop,
          soil_moisture: params.soil_moisture, soil_ph: params.soil_ph,
          N: params.N, P: params.P, K: params.K,
        })
        setData(r.data.schedule)
      } catch {}
      setLoading(false)
    }
    run()
  }, [params, trigger])

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">{t.title}</h1>
        <p className="page-sub">{t.sub} — <span className="text-accent">{params.crop}</span></p>
      </div>

      {loading && <div className="loading-overlay"><span className="spinner"/> Calculating irrigation…</div>}

      {!loading && !data && (
        <div className="loading-overlay" style={{color:'var(--text3)'}}>{t.empty}</div>
      )}

      {!loading && data && (
        <>
          <div className="grid-4 section-gap">
            {[
              { label: t.need,     value: `${data.weekly_water_need} mm`,      icon: '🪣' },
              { label: t.rain,     value: `${data.forecast_rainfall} mm`,      icon: '🌧️' },
              { label: t.net,      value: `${data.net_irrigation_need} mm`,    icon: '💧' },
              { label: t.sessions, value: data.sessions_per_week || '—',       icon: '📅' },
            ].map(s => (
              <div className="stat-card" key={s.label}>
                <span className="stat-icon">{s.icon}</span>
                <span className="stat-label">{s.label}</span>
                <span className="stat-value">{s.value}</span>
              </div>
            ))}
          </div>

          <div className="grid-2 section-gap">
            <div className="card">
              <div className="card-title"><span>📋</span>{t.plan}</div>
              <div className="irr-plan">
                {data.daily_plan.map((d, i) => (
                  <div className={`irr-day ${d.irrigate ? 'irrigate' : ''}`} key={i}>
                    <span className="irr-day-name">{d.day}</span>
                    <span className={`irr-action ${d.irrigate ? 'water' : ''}`}>{d.action}</span>
                    <span className="irr-rain">🌧 {d.rainfall}mm</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <div className="card-title"><span>💡</span>{t.tip}</div>
              <div style={{padding:'12px 0', fontSize:14, color:'var(--text)', lineHeight:1.7}}>
                {data.savings_tip}
              </div>
              <div style={{marginTop:16,padding:14,background:'rgba(34,211,165,0.07)',borderRadius:'var(--radius-sm)',border:'1px solid rgba(34,211,165,0.15)'}}>
                <div style={{fontSize:12,color:'var(--text3)',marginBottom:6}}>SCHEDULE SUMMARY</div>
                <div style={{fontSize:14,fontWeight:600,color:'var(--accent)'}}>{data.frequency}</div>
                {data.mm_per_session > 0 && (
                  <div style={{fontSize:13,color:'var(--text2)',marginTop:4}}>{data.mm_per_session} mm per session</div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
