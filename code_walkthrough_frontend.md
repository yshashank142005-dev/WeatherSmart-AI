# WeatherSmart AI — Frontend Code Walkthrough

---

## 1. [index.html](file:///C:/sem4/antigravity/demo/frontend/index.html) — HTML Shell

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800
  &family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet" />
```
**What it does:** Loads two Google Fonts: **Inter** (for body text) and **Outfit** (for headings). `display=swap` shows fallback font until Google Font loads — prevents blank text flash.

```html
<div id="root"></div>
<script type="module" src="/src/main.jsx"></script>
```
**What it does:** React will render the entire app inside `#root`. The `type="module"` enables ES module imports.

---

## 2. [main.jsx](file:///C:/sem4/antigravity/demo/frontend/src/main.jsx) — React Entry

```jsx
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode><App /></React.StrictMode>
)
```
**What it does:** Finds the `#root` div and renders the `<App>` component inside it. `StrictMode` adds extra development warnings (double-renders to catch bugs — only in dev mode).

---

## 3. [index.css](file:///C:/sem4/antigravity/demo/frontend/src/index.css) — Design System

```css
:root {
  --bg: #0a0f1e;        /* Deepest background */
  --accent: #22d3a5;     /* Primary green */
  --accent2: #6366f1;    /* Purple accent */
  ...
}
```
**What it does:** CSS custom properties (variables). Defining colors once here means changing `--accent` updates it everywhere. The dark blues + green/purple create a premium "dashboard" feel.

```css
.stat-card:hover { transform: translateY(-2px); box-shadow: var(--glow); }
```
**What it does:** Micro-animation — card lifts up 2px and gets a green glow on hover. `transition` in the base class makes it smooth.

```css
.yield-circle {
  background: conic-gradient(var(--accent) var(--pct, 0%), var(--bg3) 0%);
}
```
**What it does:** Creates a circular progress indicator using `conic-gradient`. The `--pct` variable (set via React inline style) controls how much of the circle is filled. The `::after` pseudo-element creates the inner hole (donut shape).

---

## 4. [App.jsx](file:///C:/sem4/antigravity/demo/frontend/src/App.jsx) — Root Component

```jsx
const [tab, setTab]  = useState('weather')      // Which page is shown
const [lang, setLang] = useState('en')           // EN or HI
const [params, setParams] = useState({...})      // City, crop, soil values
const [trigger, setTrigger] = useState(0)        // Increments to force re-fetch
```
**What it does:** Four pieces of state that control the entire app:
- `tab` — which panel to show
- `lang` — language for translations
- `params` — user's input values (passed to all panels)
- `trigger` — when user clicks "Run Analysis", this increments, causing all panels to re-fetch data

```jsx
const runAnalysis = useCallback(() => setTrigger(t => t + 1), [])
```
**What it does:** `useCallback` memoizes the function so it doesn't create a new reference every render (prevents unnecessary Sidebar re-renders).

```jsx
{tab === 'weather' && <WeatherPanel params={params} lang={lang} trigger={trigger} />}
```
**What it does:** Conditional rendering — only mounts the active panel. When `tab` changes, the old panel unmounts and the new one mounts fresh.

---

## 5. [Sidebar.jsx](file:///C:/sem4/antigravity/demo/frontend/src/components/Sidebar.jsx) — Navigation & Controls

```jsx
const T = {
  en: { city:'City', crop:'Crop', ... },
  hi: { city:'शहर', crop:'फसल', ... },
}
const t = T[lang]  // Pick the right language object
```
**What it does:** Simple translation system. `T[lang]` selects either English or Hindi strings. Used as `{t.city}` in JSX.

```jsx
const set = (k, v) => setParams(p => ({ ...p, [k]: v }))
```
**What it does:** Helper function that updates one field in the params object. `...p` spreads existing values, `[k]: v` uses computed property name to override just the key `k`. Example: `set('city', 'Mumbai')` → `{city:'Mumbai', crop:'wheat', ...}`.

```jsx
<input type="range" min="10" max="90" value={params.soil_moisture}
  onChange={e => set('soil_moisture', +e.target.value)} />
```
**What it does:** Range slider for soil moisture. `+e.target.value` converts string to number (the `+` unary operator). Every drag updates `params`, which propagates to all panels.

---

## 6. [WeatherPanel.jsx](file:///C:/sem4/antigravity/demo/frontend/src/components/WeatherPanel.jsx) — Weather Dashboard

```jsx
useEffect(() => {
  const fetch = async () => {
    const [c, f] = await Promise.all([
      axios.get(`/api/weather?city=${encodeURIComponent(params.city)}`),
      axios.get(`/api/forecast?city=${encodeURIComponent(params.city)}`),
    ])
    setCurrent(c.data.data)
    setForecast(f.data.data)
  }
  fetch()
}, [params.city, trigger])
```
**What it does:** `useEffect` runs when `params.city` or `trigger` changes. `Promise.all` fires BOTH API calls simultaneously (faster than sequential). `encodeURIComponent` handles cities with spaces like "New York".

```jsx
const chartData = {
  labels: forecast.map(d => new Date(d.date).toLocaleDateString('en', { weekday: 'short' })),
  datasets: [
    { label: 'Max °C', data: forecast.map(d=>d.temp_max), borderColor: '#f97316', tension: 0.4 },
    { label: 'Min °C', data: forecast.map(d=>d.temp_min), borderColor: '#22d3a5', tension: 0.4, fill: '+1' },
  ]
}
```
**What it does:** Configures Chart.js line chart. `tension: 0.4` makes curves smooth (not jagged). `fill: '+1'` fills the area between max and min lines — creating a temperature range band.

---

## 7. [PredictionsPanel.jsx](file:///C:/sem4/antigravity/demo/frontend/src/components/PredictionsPanel.jsx)

```jsx
<div className="yield-circle" style={{'--pct': pct}}>
```
**What it does:** Sets CSS variable `--pct` dynamically. The CSS `conic-gradient` uses this to fill the circle proportionally. If yield=75, then `--pct: 75%` fills 75% of the circle green.

```jsx
const fiData = {
  labels: Object.keys(pred.yield_prediction.feature_importances).map(k => k.replace('_',' ')),
  data: Object.values(...).map(v => +(v*100).toFixed(1)),
}
```
**What it does:** Transforms the ML model's feature importances into a horizontal bar chart. `Object.keys` gets feature names, `Object.values` gets importance scores. Multiply by 100 to show as percentages.

```jsx
const rankClass = r => r===1?'gold':r===2?'silver':r===3?'bronze':''
```
**What it does:** Top 3 crops get colored rank numbers (gold/silver/bronze) via CSS classes.

---

## 8. [RecommendationsPanel.jsx](file:///C:/sem4/antigravity/demo/frontend/src/components/RecommendationsPanel.jsx)

```jsx
{groups.map(priority => {
  const group = recs.filter(r => r.priority === priority)
  if (!group.length) return null
```
**What it does:** Groups recommendations by priority. Loops through ['high','medium','low'], filters matching recs, and renders each group as a card. Empty groups are skipped (`return null`).

---

## 9. [IrrigationPanel.jsx](file:///C:/sem4/antigravity/demo/frontend/src/components/IrrigationPanel.jsx)

```jsx
<div className={`irr-day ${d.irrigate ? 'irrigate' : ''}`}>
```
**What it does:** Days that need irrigation get an extra `irrigate` CSS class → green-tinted background. Non-irrigation days stay default dark.

---

## 10. [AlertsPanel.jsx](file:///C:/sem4/antigravity/demo/frontend/src/components/AlertsPanel.jsx)

```jsx
{a.type==='HEAT_WAVE'?'🌡️':a.type==='FROST'?'❄️': ...}
```
**What it does:** Ternary chain maps alert type strings to emoji icons. Each alert type gets a visually distinct icon.

---

## 11. [ChatbotPanel.jsx](file:///C:/sem4/antigravity/demo/frontend/src/components/ChatbotPanel.jsx)

```jsx
const startVoice = () => {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  const rec = new SR()
  rec.lang = lang === 'hi' ? 'hi-IN' : 'en-IN'
  rec.onresult = e => send(e.results[0][0].transcript)
  rec.start()
}
```
**What it does:** Uses the browser's built-in **Web Speech API** for voice input. `webkitSpeechRecognition` is the Chrome-prefixed version. Sets language to Hindi or English based on current lang. When speech is recognized, it automatically sends the transcribed text as a chat message.

```jsx
useEffect(() => {
  bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
}, [msgs])
```
**What it does:** Auto-scrolls chat to bottom whenever a new message is added. `?.` optional chaining prevents errors if ref isn't attached yet.

---

## How Data Flows (Big Picture)

```
User changes sidebar controls (city, crop, soil)
        ↓
App.jsx updates `params` state
        ↓
Active panel's useEffect fires (dependency: params/trigger)
        ↓
axios calls Flask API (proxied via Vite: localhost:5173/api → localhost:5000/api)
        ↓
Flask route calls weather_api + ml/model + risk_scorer
        ↓
JSON response returns to React
        ↓
setState updates → component re-renders with new data
```
