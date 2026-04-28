/**
 * api.js — Central axios instance for WeatherSmart AI.
 *
 * In development (npm run dev), VITE_API_URL is not set so baseURL defaults
 * to "" and Vite's dev-server proxy forwards /api/* to localhost:5000.
 *
 * In production (Vercel), set the environment variable:
 *   VITE_API_URL = https://your-render-backend.onrender.com
 */
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 30000,
})

export default api
