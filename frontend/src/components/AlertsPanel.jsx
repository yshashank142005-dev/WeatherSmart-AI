import { useState, useEffect, useCallback } from 'react'
import api from '../api'

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

const TOAST_VARIANT = {
  success: 'bg-emerald-900 text-emerald-100',
  warn: 'bg-amber-900 text-amber-100',
  error: 'bg-rose-900 text-rose-100',
}

const CHANNEL_STYLES = {
  active: 'border-indigo-400 bg-indigo-500/20 text-indigo-200 shadow-md shadow-indigo-500/20',
  inactive: 'border-white/10 bg-white/5 text-slate-300',
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
        const r = await api.post('/api/alert', {
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
      const r = await api.get('/api/notifications')
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
      const r = await api.post('/api/alert', {
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
    <div className="relative">

      {/* ── Toast ── */}
      {toast && (
        <div className={`fixed right-6 top-6 z-[9999] rounded-xl px-5 py-3 text-sm font-semibold text-white shadow-2xl animate-fade-in ${TOAST_VARIANT[toast.type]}`}>
          {toast.msg}
        </div>
      )}

      {/* ── Header ── */}
      <div className="page-header flex items-center justify-between gap-4">
        <div>
          <h1 className="page-title">{t.title}</h1>
          <p className="page-sub">{t.sub} — {params.city}</p>
        </div>

        {/* Bell icon */}
        <button
          onClick={() => setShowNotifs(v => !v)}
          className="relative rounded-xl border border-indigo-400/30 bg-indigo-500/15 px-3 py-2 text-2xl text-indigo-200 transition hover:bg-indigo-500/25"
          title="In-App Notifications"
        >
          🔔
          {unread > 0 && (
            <span className="absolute right-1 top-1 flex h-[18px] w-[18px] items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white">
              {unread > 9 ? '9+' : unread}
            </span>
          )}
        </button>
      </div>

      {/* ── In-App Notification Drawer ── */}
      {showNotifs && (
        <div className="card mb-5 max-h-80 overflow-y-auto">
          <div className="card-title">🔔 {t.notifTitle}</div>
          {notifs.length === 0 ? (
            <p className="text-sm text-slate-300">{t.notifEmpty}</p>
          ) : (
            notifs.map((n, i) => (
              <div
                key={i}
                className="mb-2 rounded-lg border border-white/10 bg-white/5 p-3"
                style={{ borderLeft: `3px solid ${SEVERITY_COLOR[n.severity] || '#6366f1'}` }}
              >
                <div className="mb-0.5 text-xs text-slate-300">
                  {n.timestamp} — {n.city}
                </div>
                <div className="text-sm font-semibold text-white">{n.message}</div>
                <div className="mt-0.5 text-xs text-slate-300">➜ {n.action}</div>
              </div>
            ))
          )}
        </div>
      )}

      {loading && <div className="loading-overlay"><span className="spinner" /> Checking alerts…</div>}

      {/* ── No Alerts ── */}
      {!loading && alerts.length === 0 && (
        <div className="card p-12 text-center">
          <div className="mb-3 text-5xl">✅</div>
          <div className="text-base text-slate-300">{t.none}</div>
        </div>
      )}

      {/* ── Alert Cards ── */}
      {!loading && alerts.length > 0 && (
        <div className="alert-list section-gap">
          {alerts.map((a, i) => (
            <div className={`alert-item ${a.severity}`} key={i}>
              <div className="shrink-0 text-3xl">{ALERT_ICON[a.type] || '⚠️'}</div>
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
      <div className="card mt-6">
        <div className="card-title"><span>📡</span> {t.channels}</div>

        {/* Channel toggles */}
        <div className="mb-4 flex flex-wrap gap-2.5">
          {[
            { key: 'inapp', icon: '🔔', label: t.inapp },
            { key: 'email', icon: '📧', label: t.emailLabel },
            { key: 'sms',   icon: '📱', label: t.sms },
          ].map(({ key, icon, label }) => (
            <button
              key={key}
              onClick={() => toggleChannel(key)}
              className={`rounded-full border-2 px-4 py-2 text-sm font-semibold transition ${channels[key] ? CHANNEL_STYLES.active : CHANNEL_STYLES.inactive}`}
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
            className="mb-2.5 w-full rounded-xl border border-white/10 bg-white/5 px-3.5 py-2.5 text-sm text-white outline-none transition placeholder:text-slate-400 focus:border-indigo-300/50 focus:ring-2 focus:ring-indigo-300/20"
          />
        )}

        {/* Phone input */}
        {channels.sms && (
          <input
            type="tel"
            placeholder={t.phone}
            value={phone}
            onChange={e => setPhone(e.target.value)}
            className="mb-2.5 w-full rounded-xl border border-white/10 bg-white/5 px-3.5 py-2.5 text-sm text-white outline-none transition placeholder:text-slate-400 focus:border-indigo-300/50 focus:ring-2 focus:ring-indigo-300/20"
          />
        )}

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={sending}
          className={`rounded-xl px-6 py-2.5 text-sm font-bold text-white transition ${
            sending
              ? 'cursor-not-allowed bg-indigo-500/40 opacity-70'
              : 'bg-gradient-to-r from-indigo-500 to-violet-500 shadow-lg shadow-indigo-500/30 hover:-translate-y-0.5'
          }`}
        >
          {sending ? `⏳ ${t.sending}` : `🚀 ${t.send}`}
        </button>

        {/* Dispatch Results */}
        {dispResult && (
          <div className="mt-4">
            <div className="mb-2 text-sm font-bold text-slate-300">
              {t.dispatchTitle}
            </div>
            {Object.entries(dispResult).map(([ch, res]) => (
              <div
                key={ch}
                className={`mb-1.5 flex items-center gap-2.5 rounded-xl border px-3 py-2 ${
                  res.success
                    ? 'border-emerald-400/30 bg-emerald-400/10'
                    : 'border-rose-400/30 bg-rose-400/10'
                }`}
              >
                <span className="text-base">
                  {ch === 'email' ? '📧' : ch === 'sms' ? '📱' : '🔔'}
                </span>
                <span className="text-sm font-semibold capitalize text-white">{ch}</span>
                <span className={`text-xs ${res.success ? 'text-emerald-200' : 'text-rose-200'}`}>
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
