import { useState, useEffect } from 'react'
import api from '../api'
import { Bar } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

const T = {
  en: { title:'ML Predictions', sub:'Random Forest yield index & crop suitability ranking', yield:'Yield Prediction', suit:'Crop Suitability Ranking', conf:'Confidence', interp:'Interpretation', r2:'Model R²', feature:'Feature Importance' },
  hi: { title:'ML पूर्वानुमान', sub:'Random Forest उपज सूचकांक', yield:'उपज पूर्वानुमान', suit:'फसल उपयुक्तता रैंकिंग', conf:'आत्मविश्वास', interp:'व्याख्या', r2:'मॉडल R²', feature:'फीचर महत्त्व' },
}

const rankClass = r => r===1?'gold':r===2?'silver':r===3?'bronze':''

export default function PredictionsPanel({ params, lang, trigger }) {
  const [pred, setPred]     = useState(null)
  const [suit, setSuit]     = useState([])
  const [loading, setLoading] = useState(false)
  const t = T[lang]

  useEffect(() => {
    const run = async () => {
      setLoading(true)
      try {
        const body = {
          city: params.city, crop: params.crop,
          soil_moisture: params.soil_moisture, soil_ph: params.soil_ph,
          N: params.N, P: params.P, K: params.K,
        }
        const [p, s] = await Promise.all([
          api.post('/api/predict', body),
          api.post('/api/suitability', body),
        ])
        setPred(p.data)
        setSuit(s.data.rankings)
      } catch {}
      setLoading(false)
    }
    run()
  }, [params, trigger])

  const pct = pred ? `${pred.yield_prediction.yield_index}%` : '0%'

  const fiData = pred ? {
    labels: Object.keys(pred.yield_prediction.feature_importances).map(k => k.replace('_',' ')),
    datasets: [{
      label: 'Importance',
      data: Object.values(pred.yield_prediction.feature_importances).map(v => +(v*100).toFixed(1)),
      backgroundColor: ['#22d3a5','#6366f1','#f59e0b','#f97316','#60a5fa','#a78bfa','#34d399'],
      borderRadius: 6,
    }]
  } : null

  const fiOpts = {
    indexAxis: 'y', responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: '#64748b', callback: v => v+'%' }, grid: { color: 'rgba(255,255,255,0.04)' } },
      y: { ticks: { color: '#94a3b8' }, grid: { display: false } },
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">{t.title}</h1>
        <p className="page-sub">{t.sub}</p>
      </div>

      {loading && <div className="loading-overlay"><span className="spinner"/> Running ML model…</div>}

      {pred && !loading && (
        <div className="grid-2 section-gap">
          {/* Yield Card */}
          <div className="card">
            <div className="card-title"><span>🌾</span>{t.yield} — {params.crop}</div>
            <div className="yield-display">
              <div className="yield-circle" style={{'--pct': pct}}>
                <span className="yield-num">{pred.yield_prediction.yield_index}</span>
                <span className="yield-sub">/100</span>
              </div>
              <span className="yield-label">{pred.yield_prediction.interpretation}</span>
            </div>
            <div style={{marginTop:16,display:'flex',flexDirection:'column',gap:8}}>
              {[
                [t.conf, `${pred.yield_prediction.confidence}%`],
                [t.r2,   pred.yield_prediction.model_r2],
                ['Climate Risk', pred.climate_risk.level.toUpperCase()],
                ['Pest Risk',    pred.pest_risk.level.toUpperCase()],
              ].map(([k,v]) => (
                <div className="flex-between" key={k} style={{fontSize:13}}>
                  <span style={{color:'var(--text2)'}}>{k}</span>
                  <span style={{fontWeight:600,color:'var(--accent)'}}>{v}</span>
                </div>
              ))}
            </div>
            {pred.climate_risk.factors.length > 0 && (
              <div style={{marginTop:12}}>
                {pred.climate_risk.factors.map(f => (
                  <div key={f} style={{fontSize:12,color:'var(--text2)',padding:'3px 0'}}>• {f}</div>
                ))}
              </div>
            )}
          </div>

          {/* Feature Importance */}
          {fiData && (
            <div className="card">
              <div className="card-title"><span>📊</span>{t.feature}</div>
              <Bar data={fiData} options={fiOpts} />
            </div>
          )}
        </div>
      )}

      {suit.length > 0 && !loading && (
        <div className="card">
          <div className="card-title"><span>🏆</span>{t.suit}</div>
          <div className="suit-list">
            {suit.map(s => (
              <div className="suit-item" key={s.crop}>
                <span className={`suit-rank ${rankClass(s.rank)}`}>#{s.rank}</span>
                <span className="suit-crop">{s.crop}</span>
                <div className="suit-bar-wrap">
                  <div className="suit-bar" style={{width:`${s.yield_index}%`}} />
                </div>
                <span className="suit-score">{s.yield_index}</span>
                <span className={`badge badge-${s.suitability==='Excellent'?'low':s.suitability==='Good'?'low':s.suitability==='Moderate'?'medium':'high'}`}>{s.suitability}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
