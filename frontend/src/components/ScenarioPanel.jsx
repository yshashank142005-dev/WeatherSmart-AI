import { useState, useEffect, useRef, useCallback } from 'react'
import api from '../api'

/* ── i18n ─────────────────────────────────────────────────────────── */
const T = {
  en: {
    title: 'What-If Scenario Engine',
    sub: 'Adjust temperature & rainfall — see instant yield impact',
    tempDelta: 'Temperature Change',
    rainDelta: 'Rainfall Change',
    original: 'Current Conditions',
    scenario: 'Modified Scenario',
    climateRisk: 'Climate Risk',
    pestRisk: 'Pest Risk',
    confidence: 'Confidence',
    insights: 'Scenario Insights',
    improvement: 'improvement',
    decline: 'decline',
    noChange: 'no change',
    factors: 'Risk Factors',
    resetBtn: 'Reset',
  },
  hi: {
    title: 'क्या-अगर परिदृश्य इंजन',
    sub: 'तापमान और वर्षा बदलें — तुरंत उपज प्रभाव देखें',
    tempDelta: 'तापमान परिवर्तन',
    rainDelta: 'वर्षा परिवर्तन',
    original: 'वर्तमान स्थिति',
    scenario: 'संशोधित परिदृश्य',
    climateRisk: 'जलवायु जोखिम',
    pestRisk: 'कीट जोखिम',
    confidence: 'आत्मविश्वास',
    insights: 'परिदृश्य अंतर्दृष्टि',
    improvement: 'सुधार',
    decline: 'गिरावट',
    noChange: 'कोई बदलाव नहीं',
    factors: 'जोखिम कारक',
    resetBtn: 'रीसेट',
  },
}

/* ── RiskBadge ────────────────────────────────────────────────────── */
function RiskBadge({ level }) {
  const cls = level === 'low' ? 'badge-low' : level === 'medium' ? 'badge-medium' : 'badge-high'
  return <span className={`badge ${cls}`}>{level.toUpperCase()}</span>
}

/* ── DeltaSlider ──────────────────────────────────────────────────── */
function DeltaSlider({ label, value, onChange, min, max, step, unit, icon, accentColor }) {
  const pctRaw = ((value - min) / (max - min)) * 100
  const neutral = ((0 - min) / (max - min)) * 100
  const isPos   = value > 0
  const isNeg   = value < 0
  const valColor = isPos ? '#4ade80' : isNeg ? '#f87171' : 'var(--text3)'

  return (
    <div className="wi-slider-card" style={{ '--wi-accent': accentColor }}>
      <div className="wi-slider-header">
        <span className="wi-slider-icon">{icon}</span>
        <span className="wi-slider-label">{label}</span>
        <span className="wi-delta-val" style={{ color: valColor }}>
          {value > 0 ? '+' : ''}{value}{unit}
        </span>
      </div>

      <div className="wi-control-row">
        <button
          className="wi-step-btn"
          onClick={() => onChange(Math.max(min, +(value - step).toFixed(1)))}
          aria-label="decrease"
        >−</button>

        <div className="wi-range-wrap">
          {/* neutral-zero tick mark */}
          <div className="wi-zero-tick" style={{ left: `${neutral}%` }} />
          <input
            type="range"
            min={min} max={max} step={step}
            value={value}
            onChange={e => onChange(+e.target.value)}
            className="wi-range-input"
            style={{ '--wi-pct': `${pctRaw}%`, '--wi-neutral': `${neutral}%` }}
          />
        </div>

        <button
          className="wi-step-btn"
          onClick={() => onChange(Math.min(max, +(value + step).toFixed(1)))}
          aria-label="increase"
        >+</button>
      </div>

      <div className="wi-markers">
        <span>{min}{unit}</span>
        <span style={{ fontSize: 10, color: 'var(--text3)' }}>0 = no change</span>
        <span>+{max}{unit}</span>
      </div>
    </div>
  )
}

/* ── YieldCircle ──────────────────────────────────────────────────── */
function YieldCircle({ value, ringColor }) {
  return (
    <div
      className="wi-yield-circle"
      style={{
        '--pct':   `${value}%`,
        '--ring':  ringColor || 'var(--accent)',
      }}
    >
      <span className="wi-yield-num" style={{ color: ringColor || 'var(--accent)' }}>
        {value}
      </span>
      <span className="wi-yield-sub">/100</span>
    </div>
  )
}

/* ── CompareCard ──────────────────────────────────────────────────── */
function CompareCard({ label, badgeStyle, data, yieldDelta, t }) {
  const { weather, yield_prediction: yp, climate_risk: cr, pest_risk: pr } = data

  const ringColor =
    yieldDelta === undefined ? 'var(--accent)' :
    yieldDelta > 0 ? '#4ade80' :
    yieldDelta < 0 ? '#f87171' :
    'var(--accent)'

  return (
    <div className={`wi-card ${yieldDelta !== undefined ? (yieldDelta > 0 ? 'wi-improved' : yieldDelta < 0 ? 'wi-degraded' : '') : ''}`}>
      {/* Header */}
      <div className="wi-card-header">
        <span className="wi-card-badge" style={badgeStyle}>{label}</span>
        <span className="wi-card-meta">
          {weather.temperature}°C · {weather.rainfall}mm
        </span>
      </div>

      {/* Yield circle */}
      <div className="wi-circle-wrap">
        <YieldCircle value={yp.yield_index} ringColor={ringColor} />
        {yieldDelta !== undefined && yieldDelta !== 0 && (
          <span
            className="wi-delta-tag"
            style={{
              color:       yieldDelta > 0 ? '#4ade80' : '#f87171',
              borderColor: yieldDelta > 0 ? '#4ade80' : '#f87171',
            }}
          >
            {yieldDelta > 0 ? '↑' : '↓'} {Math.abs(yieldDelta)} pts
          </span>
        )}
      </div>

      {/* Interpretation */}
      <p className="wi-interp">{yp.interpretation}</p>

      {/* Metrics */}
      <div className="wi-metrics">
        {[
          [t.confidence,  `${yp.confidence}%`],
          [t.climateRisk, <RiskBadge key="cr" level={cr.level} />],
          [t.pestRisk,    <RiskBadge key="pr" level={pr.level} />],
        ].map(([k, v]) => (
          <div className="wi-metric-row" key={k}>
            <span className="wi-metric-label">{k}</span>
            {typeof v === 'string'
              ? <span className="wi-metric-val">{v}</span>
              : v}
          </div>
        ))}
      </div>

      {/* Factors */}
      {cr.factors.slice(0, 2).map(f => (
        <div className="wi-factor" key={f}>• {f}</div>
      ))}
    </div>
  )
}

/* ── Main ScenarioPanel ───────────────────────────────────────────── */
export default function ScenarioPanel({ params, lang, trigger }) {
  const t = T[lang]

  const [tempDelta, setTempDelta] = useState(0)
  const [rainDelta, setRainDelta] = useState(0)
  const [result,    setResult]    = useState(null)
  const [loading,   setLoading]   = useState(false)
  const debounceRef = useRef(null)

  const fetchScenario = useCallback(async (td, rd) => {
    setLoading(true)
    try {
      const { data } = await api.post('/api/whatif', {
        city:          params.city,
        crop:          params.crop,
        soil_moisture: params.soil_moisture,
        soil_ph:       params.soil_ph,
        N:             params.N,
        P:             params.P,
        K:             params.K,
        temp_delta:    td,
        rain_delta:    rd,
      })
      setResult(data)
    } catch (err) {
      console.error('what-if fetch failed:', err)
    }
    setLoading(false)
  }, [params])

  /* Debounce slider changes → 350 ms */
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => fetchScenario(tempDelta, rainDelta), 350)
    return () => clearTimeout(debounceRef.current)
  }, [tempDelta, rainDelta, fetchScenario])

  /* Re-fetch when sidebar params / trigger change */
  useEffect(() => {
    fetchScenario(tempDelta, rainDelta)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params, trigger])

  const reset = () => { setTempDelta(0); setRainDelta(0) }

  const yd = result?.yield_delta ?? 0
  const deltaColor = yd > 0 ? '#4ade80' : yd < 0 ? '#f87171' : 'var(--text3)'

  return (
    <div id="whatif-panel">
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">🔮 {t.title}</h1>
        <p className="page-sub">{t.sub}</p>
      </div>

      {/* ── Sliders ─────────────────────────────────────────────── */}
      <div className="wi-sliders">
        <DeltaSlider
          label={t.tempDelta}
          value={tempDelta}
          onChange={setTempDelta}
          min={-15} max={15} step={1}
          unit="°C" icon="🌡️"
          accentColor="#f97316"
        />
        <DeltaSlider
          label={t.rainDelta}
          value={rainDelta}
          onChange={setRainDelta}
          min={-50} max={50} step={5}
          unit="mm" icon="🌧️"
          accentColor="#60a5fa"
        />
      </div>

      {/* Reset button */}
      {(tempDelta !== 0 || rainDelta !== 0) && (
        <button className="wi-reset-btn" onClick={reset}>↺ {t.resetBtn}</button>
      )}

      {/* ── Loading ──────────────────────────────────────────────── */}
      {loading && (
        <div className="loading-overlay">
          <span className="spinner" /> Computing scenario…
        </div>
      )}

      {/* ── Results ──────────────────────────────────────────────── */}
      {result && !loading && (
        <>
          {/* Summary bar */}
          <div className="wi-summary-bar">
            <div className="wi-pills">
              <span className="wi-pill">🌡️ {result.original.weather.temperature}°C → {result.scenario.weather.temperature}°C</span>
              <span className="wi-pill">🌧️ {result.original.weather.rainfall}mm → {result.scenario.weather.rainfall}mm</span>
              <span className="wi-pill">🌾 {params.crop.charAt(0).toUpperCase() + params.crop.slice(1)}</span>
            </div>
            <div className="wi-yield-delta" style={{ color: deltaColor, borderColor: deltaColor }}>
              {yd > 0 ? '↑' : yd < 0 ? '↓' : '→'}
              <span style={{ marginLeft: 4 }}>{Math.abs(yd)} pts</span>
              <span style={{ fontSize: 11, opacity: 0.75, marginLeft: 4 }}>
                {yd > 0 ? t.improvement : yd < 0 ? t.decline : t.noChange}
              </span>
            </div>
          </div>

          {/* Comparison */}
          <div className="wi-compare-grid">
            <CompareCard
              label={`📍 ${t.original}`}
              badgeStyle={{ background: 'rgba(34,211,165,0.1)', color: 'var(--accent)', borderColor: 'rgba(34,211,165,0.3)' }}
              data={result.original}
              t={t}
            />

            <div className="wi-vs">
              <div className="wi-vs-line" />
              <div className="wi-vs-badge">VS</div>
              <div className="wi-vs-line" />
            </div>

            <CompareCard
              label={`🔮 ${t.scenario}`}
              badgeStyle={{ background: 'rgba(99,102,241,0.12)', color: 'var(--accent2)', borderColor: 'rgba(99,102,241,0.3)' }}
              data={result.scenario}
              yieldDelta={yd}
              t={t}
            />
          </div>

          {/* Crop-specific insight strip */}
          {result.scenario.climate_risk.crop_specific_notes?.length > 0 && (
            <div className="card mt-16">
              <div className="card-title"><span>💡</span>{t.insights}</div>
              {result.scenario.climate_risk.crop_specific_notes.map(n => (
                <div key={n} className="wi-insight-row">{n}</div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
