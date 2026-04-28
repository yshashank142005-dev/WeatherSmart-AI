import { useState, useEffect } from 'react'
import api from '../api'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  PointElement, LineElement, Tooltip, Legend, Filler
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler)

const ICON_MAP = { '01d':'☀️','01n':'🌙','02d':'⛅','02n':'⛅','03d':'☁️','03n':'☁️','04d':'☁️','04n':'☁️','09d':'🌧️','09n':'🌧️','10d':'🌦️','10n':'🌧️','11d':'⛈️','13d':'❄️','50d':'🌫️' }
const wi = code => ICON_MAP[code] || '🌤️'

const T = {
  en: { title:'Weather Dashboard', sub:'Real-time conditions & 7-day forecast', forecast:'7-Day Forecast', temp:'Temperature', humidity:'Humidity', wind:'Wind', rain:'Rainfall', uv:'UV Index', pressure:'Pressure', vis:'Visibility', feels:'Feels Like' },
  hi: { title:'मौसम डैशबोर्ड', sub:'वास्तविक समय की जानकारी', forecast:'7-दिन पूर्वानुमान', temp:'तापमान', humidity:'आर्द्रता', wind:'हवा', rain:'वर्षा', uv:'UV सूचकांक', pressure:'दबाव', vis:'दृश्यता', feels:'महसूस होता है' },
}

export default function WeatherPanel({ params, lang, trigger }) {
  const [current, setCurrent] = useState(null)
  const [forecast, setForecast] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const t = T[lang]

  useEffect(() => {
    const fetchWeather = async () => {
      setLoading(true)
      setError(null)
      try {
        const [c, f] = await Promise.all([
          api.get(`/api/weather?city=${encodeURIComponent(params.city)}`),
          api.get(`/api/forecast?city=${encodeURIComponent(params.city)}`),

        ])
        if (!c.data.success) throw new Error(c.data.error || 'Weather fetch failed')
        setCurrent(c.data.data)
        setForecast(f.data.data)
      } catch (err) {
        setError(err.message || 'Failed to fetch weather data. Check your API key or city name.')
        setCurrent(null)
        setForecast([])
      }
      setLoading(false)
    }
    fetchWeather()
  }, [params.city, trigger])

  const chartData = {
    labels: forecast.map(d => new Date(d.date).toLocaleDateString('en', { weekday: 'short' })),
    datasets: [
      { label: 'Max °C', data: forecast.map(d=>d.temp_max), borderColor: '#f97316', backgroundColor: 'rgba(249,115,22,0.1)', tension: 0.4, fill: false },
      { label: 'Min °C', data: forecast.map(d=>d.temp_min), borderColor: '#22d3a5', backgroundColor: 'rgba(34,211,165,0.1)', tension: 0.4, fill: '+1' },
    ]
  }
  const chartOpts = {
    responsive: true, plugins: { legend: { labels: { color:'#94a3b8', font:{size:12} } }, tooltip:{mode:'index'} },
    scales: {
      x: { ticks:{color:'#64748b'}, grid:{color:'rgba(255,255,255,0.04)'} },
      y: { ticks:{color:'#64748b'}, grid:{color:'rgba(255,255,255,0.04)'} },
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">{t.title} <span>— {params.city}</span></h1>
        <p className="page-sub">{t.sub}</p>
      </div>

      {loading && <div className="loading-overlay"><span className="spinner"/> Loading weather…</div>}

      {error && !loading && (
        <div style={{
          background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.4)',
          borderRadius: '12px', padding: '16px 20px', marginBottom: '20px',
          color: '#fca5a5', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '14px'
        }}>
          <span style={{fontSize:'20px'}}>⚠️</span>
          <div>
            <strong>Weather data unavailable</strong><br/>
            <span style={{opacity:0.8}}>{error}</span>
          </div>
        </div>
      )}

      {current && !loading && (
        <>
          <div className="grid-4 section-gap">
            {[
              { icon:'🌡️', label:t.temp,     value:current.temperature, unit:'°C' },
              { icon:'💧', label:t.humidity,  value:current.humidity,    unit:'%' },
              { icon:'💨', label:t.wind,      value:current.wind_speed,  unit:'km/h' },
              { icon:'🌧️', label:t.rain,      value:current.rainfall,    unit:'mm' },
              { icon:'☀️', label:t.uv,        value:current.uv_index,    unit:'' },
              { icon:'🔵', label:t.pressure,  value:current.pressure,    unit:'hPa' },
              { icon:'👁️', label:t.vis,       value:current.visibility,  unit:'km' },
              { icon:'🌡️', label:t.feels,     value:current.feels_like,  unit:'°C' },
            ].map(s => (
              <div className="stat-card" key={s.label}>
                <span className="stat-icon">{s.icon}</span>
                <span className="stat-label">{s.label}</span>
                <span className="stat-value">{s.value}<span className="stat-unit"> {s.unit}</span></span>
              </div>
            ))}
          </div>

          <div className="card section-gap">
            <div className="card-title"><span>📅</span>{t.forecast}</div>
            <div className="forecast-grid">
              {forecast.map(d => (
                <div className="forecast-day" key={d.date}>
                  <span className="day-name">{new Date(d.date).toLocaleDateString('en',{weekday:'short'})}</span>
                  <span className="day-icon">{wi(d.icon)}</span>
                  <span className="day-temp">{d.temp_max}° / {d.temp_min}°</span>
                  <span className="day-rain">🌧 {d.rainfall}mm</span>
                  <span style={{fontSize:10,color:'var(--text3)'}}>{d.description}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <div className="card-title"><span>📈</span>Temperature Trend</div>
            <Line data={chartData} options={chartOpts} />
          </div>
        </>
      )}
    </div>
  )
}
