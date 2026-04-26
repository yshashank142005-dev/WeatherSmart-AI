import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

const T = {
  en: {
    title: 'Weather Alerts',
    sub: 'Real-time extreme event notifications',
    none: '✅ No active alerts for current conditions.',
    action: 'Recommended Action',
    channels: 'Send Notifications',
    send: 'Send Alerts',
    sending: 'Sending…',
    email: 'Email Address',
    phone: 'Phone (E.164 format, e.g. +919876543210)',
    inapp: 'In-App',
    sms: 'SMS',
    emailLabel: 'Email',
    noAlerts: 'No alerts to send — conditions are safe.',
    notifTitle: '🔔 Notification Log',
    notifEmpty: 'No notifications yet.',
    dispatchTitle: 'Dispatch Results',
  },
  hi: {
    title: 'मौसम अलर्ट',
    sub: 'रीयल-टाइम चरम घटना अधिसूचनाएं',
    none: '✅ वर्तमान परिस्थितियों के लिए कोई सक्रिय अलर्ट नहीं।',
    action: 'अनुशंसित कार्रवाई',
    channels: 'अधिसूचनाएं भेजें',
    send: 'अलर्ट भेजें',
    sending: 'भेजा जा रहा है…',
    email: 'ईमेल पता',
    phone: 'फ़ोन (+91XXXXXXXXXX)',
    inapp: 'ऐप में',
    sms: 'SMS',
    emailLabel: 'ईमेल',
    noAlerts: 'कोई अलर्ट नहीं — परिस्थितियाँ सुरक्षित हैं।',
    notifTitle: '🔔 अधिसूचना लॉग',
    notifEmpty: 'अभी तक कोई अधिसूचना नहीं।',
    dispatchTitle: 'डिस्पैच परिणाम',
  },
}

const SEVERITY_COLOR = {
  critical: '#ef4444',
  high:     '#f97316',
  medium:   '#eab308',
  low:      '#22c55e',
}

const ALERT_ICON = {
  HEAT_WAVE:     '🌡️',
  FROST:         '❄️',
  HEAVY_RAIN:    '🌧️',
  STRONG_WIND:   '💨',
  HIGH_HUMIDITY: '💧',
}

export default function AlertsPanel({ params, lang, trigger }) {
  const t = T[lang]

  // ── State ─────────────────────────────────────────────────────────────────
  const [alerts,     setAlerts]     = useState([])
  const [loading,    setLoading]    = useState(false)
  const [channels,   setChannels]   = useState({ inapp: true, email: false, sms: false })
  const [email,      setEmail]      = useState('')
  const [phone,      setPhone]      = useState('')
  const [sending,    setSending]    = useState(false)
  const [dispResult, setDispResult] = useState(null)
  const [notifs,     setNotifs]     = useState([])
  const [unread,     setUnread]     = useState(0)
  const [showNotifs, setShowNotifs] = useState(false)
  const [toast,      setToast]      = useState(null)

  // ── Fetch alerts on param change ──────────────────────────────────────────
  useEffect(() => {
    const run = async () => {
      setLoading(true)
      setDispResult(null)
      try {
        const r = await axios.post('/api/alert', {
          city:     params.city,
          crop:     params.crop,
          channels: ['inapp'],   // auto-dispatch in-app on load
        })
        setAlerts(r.data.alerts || [])
      } catch {}
      setLoading(false)
    }
    run()
  }, [params, trigger])

  // ── Poll in-app notification feed every 10s ───────────────────────────────
  const fetchNotifs = useCallback(async () => {
    try {
      const r = await axios.get('/api/notifications')
      setNotifs(r.data.notifications || [])
      setUnread(r.data.unread || 0)
    } catch {}
  }, [])

  useEffect(() => {
    fetchNotifs()
    const id = setInterval(fetchNotifs, 10000)
    return () => clearInterval(id)
  }, [fetchNotifs])

  // ── Send notifications ────────────────────────────────────────────────────
  const handleSend = async () => {
    if (!alerts.length) {
      showToast('⚠️ No alerts to dispatch — conditions are currently safe.', 'warn')
      return
    }
    setSending(true)
    setDispResult(null)
    try {
      const activeChannels = Object.entries(channels).filter(([, v]) => v).map(([k]) => k)
      const r = await axios.post('/api/alert', {
        city:     params.city,
        crop:     params.crop,
        email:    channels.email  ? email : '',
        phone:    channels.sms    ? phone : '',
        channels: activeChannels,
      })
      setDispResult(r.data.dispatch_results || {})
      fetchNotifs()
      showToast('✅ Notifications dispatched!', 'success')
    } catch (err) {
      showToast('❌ Failed to send notifications.', 'error')
    }
    setSending(false)
  }

  const showToast = (msg, type) => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 4000)
  }

  const toggleChannel = (ch) => setChannels(prev => ({ ...prev, [ch]: !prev[ch] }))

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div style={{ position: 'relative' }}>

      {/* ── Toast ── */}
      {toast && (
        <div style={{
          position: 'fixed', top: 24, right: 24, zIndex: 9999,
          padding: '14px 20px', borderRadius: 10, fontWeight: 600, fontSize: 14,
          background: toast.type === 'success' ? '#166534' : toast.type === 'warn' ? '#92400e' : '#7f1d1d',
          color: '#fff', boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
          animation: 'fadeIn 0.3s ease',
        }}>
          {toast.msg}
        </div>
      )}

      {/* ── Header ── */}
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 className="page-title">{t.title}</h1>
          <p className="page-sub">{t.sub} — {params.city}</p>
        </div>

        {/* Bell icon */}
        <button
          onClick={() => setShowNotifs(v => !v)}
          style={{
            position: 'relative', background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.3)',
            borderRadius: 10, padding: '10px 14px', cursor: 'pointer', fontSize: 22, color: '#a5b4fc',
            transition: 'all 0.2s',
          }}
          title="In-App Notifications"
        >
          🔔
          {unread > 0 && (
            <span style={{
              position: 'absolute', top: 4, right: 4, background: '#ef4444',
              color: '#fff', borderRadius: '50%', width: 18, height: 18,
              fontSize: 10, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              {unread > 9 ? '9+' : unread}
            </span>
          )}
        </button>
      </div>

      {/* ── In-App Notification Drawer ── */}
      {showNotifs && (
        <div className="card" style={{ marginBottom: 20, maxHeight: 320, overflowY: 'auto' }}>
          <div className="card-title">🔔 {t.notifTitle}</div>
          {notifs.length === 0 ? (
            <p style={{ color: 'var(--text2)', fontSize: 14 }}>{t.notifEmpty}</p>
          ) : (
            notifs.map((n, i) => (
              <div key={i} style={{
                padding: '10px 12px', marginBottom: 8,
                borderLeft: `3px solid ${SEVERITY_COLOR[n.severity] || '#6366f1'}`,
                background: 'rgba(255,255,255,0.03)', borderRadius: 6,
              }}>
                <div style={{ fontSize: 12, color: 'var(--text2)', marginBottom: 2 }}>
                  {n.timestamp} — {n.city}
                </div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{n.message}</div>
                <div style={{ fontSize: 12, color: 'var(--text2)', marginTop: 2 }}>➜ {n.action}</div>
              </div>
            ))
          )}
        </div>
      )}

      {loading && <div className="loading-overlay"><span className="spinner" /> Checking alerts…</div>}

      {/* ── No Alerts ── */}
      {!loading && alerts.length === 0 && (
        <div className="card" style={{ textAlign: 'center', padding: 48 }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>✅</div>
          <div style={{ fontSize: 16, color: 'var(--text2)' }}>{t.none}</div>
        </div>
      )}

      {/* ── Alert Cards ── */}
      {!loading && alerts.length > 0 && (
        <div className="alert-list section-gap">
          {alerts.map((a, i) => (
            <div className={`alert-item ${a.severity}`} key={i}>
              <div style={{ fontSize: 28, flexShrink: 0 }}>{ALERT_ICON[a.type] || '⚠️'}</div>
              <div className="alert-body">
                <div className="alert-title">{a.message}</div>
                <div className="alert-action">➜ {a.action}</div>
              </div>
              <span className={`badge badge-${a.severity}`}>{a.severity}</span>
            </div>
          ))}
        </div>
      )}

      {/* ── Notification Dispatch Panel ── */}
      <div className="card" style={{ marginTop: 24 }}>
        <div className="card-title"><span>📡</span> {t.channels}</div>

        {/* Channel toggles */}
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
          {[
            { key: 'inapp', icon: '🔔', label: t.inapp },
            { key: 'email', icon: '📧', label: t.emailLabel },
            { key: 'sms',   icon: '📱', label: t.sms },
          ].map(({ key, icon, label }) => (
            <button
              key={key}
              onClick={() => toggleChannel(key)}
              style={{
                padding: '8px 18px', borderRadius: 20, cursor: 'pointer',
                fontWeight: 600, fontSize: 13, transition: 'all 0.2s',
                background:   channels[key] ? 'rgba(99,102,241,0.25)' : 'rgba(255,255,255,0.05)',
                border:       channels[key] ? '2px solid #6366f1'     : '2px solid rgba(255,255,255,0.1)',
                color:        channels[key] ? '#a5b4fc'               : 'var(--text2)',
                boxShadow:    channels[key] ? '0 0 12px rgba(99,102,241,0.25)' : 'none',
              }}
            >
              {icon} {label}
            </button>
          ))}
        </div>

        {/* Email input */}
        {channels.email && (
          <input
            type="email"
            placeholder={t.email}
            value={email}
            onChange={e => setEmail(e.target.value)}
            style={{
              width: '100%', padding: '10px 14px', marginBottom: 10,
              background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 8, color: 'var(--text1)', fontSize: 14, outline: 'none', boxSizing: 'border-box',
            }}
          />
        )}

        {/* Phone input */}
        {channels.sms && (
          <input
            type="tel"
            placeholder={t.phone}
            value={phone}
            onChange={e => setPhone(e.target.value)}
            style={{
              width: '100%', padding: '10px 14px', marginBottom: 10,
              background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 8, color: 'var(--text1)', fontSize: 14, outline: 'none', boxSizing: 'border-box',
            }}
          />
        )}

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={sending}
          style={{
            padding: '11px 28px', borderRadius: 8, cursor: sending ? 'not-allowed' : 'pointer',
            background: sending ? 'rgba(99,102,241,0.3)' : 'linear-gradient(135deg,#6366f1,#8b5cf6)',
            border: 'none', color: '#fff', fontWeight: 700, fontSize: 14,
            boxShadow: '0 4px 16px rgba(99,102,241,0.3)', transition: 'all 0.2s',
            opacity: sending ? 0.7 : 1,
          }}
        >
          {sending ? `⏳ ${t.sending}` : `🚀 ${t.send}`}
        </button>

        {/* Dispatch Results */}
        {dispResult && (
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text2)', marginBottom: 8 }}>
              {t.dispatchTitle}
            </div>
            {Object.entries(dispResult).map(([ch, res]) => (
              <div key={ch} style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '8px 12px', marginBottom: 6, borderRadius: 8,
                background: res.success ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
                border: `1px solid ${res.success ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
              }}>
                <span style={{ fontSize: 16 }}>
                  {ch === 'email' ? '📧' : ch === 'sms' ? '📱' : '🔔'}
                </span>
                <span style={{ fontSize: 13, fontWeight: 600, textTransform: 'capitalize' }}>{ch}</span>
                <span style={{ fontSize: 12, color: res.success ? '#86efac' : '#fca5a5' }}>
                  {res.success ? '✅' : '❌'} {res.message}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  )
}
