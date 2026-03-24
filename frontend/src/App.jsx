import { useState, useEffect } from 'react'
import Chat from './components/Chat.jsx'

// Simple user ID — in production this would come from auth
const USER_ID = 'demo_user'

export default function App() {
  const [stravaConnected, setStravaConnected] = useState(false)

  useEffect(() => {
    fetch(`/api/strava/status?user_id=${USER_ID}`)
      .then(r => r.json())
      .then(d => setStravaConnected(d.connected))
      .catch(() => {})

    // Handle redirect back from Strava
    if (window.location.search.includes('strava=connected')) {
      setStravaConnected(true)
      window.history.replaceState({}, '', '/')
    }
  }, [])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <header style={{
        background: '#1a1d27',
        borderBottom: '1px solid #2a2d3a',
        padding: '12px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 22 }}>🏊‍♂️🚴‍♂️🏃‍♂️</span>
          <span style={{ fontWeight: 700, fontSize: 18 }}>Triathlon Coach</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {stravaConnected ? (
            <span style={{
              background: '#1a3a2a',
              color: '#4ade80',
              border: '1px solid #22c55e44',
              borderRadius: 20,
              padding: '4px 12px',
              fontSize: 13,
            }}>
              ✓ Strava connected
            </span>
          ) : (
            <a
              href={`/api/strava/auth?user_id=${USER_ID}`}
              style={{
                background: '#fc4c02',
                color: '#fff',
                border: 'none',
                borderRadius: 20,
                padding: '6px 14px',
                fontSize: 13,
                fontWeight: 600,
                textDecoration: 'none',
                cursor: 'pointer',
              }}
            >
              Connect Strava
            </a>
          )}
        </div>
      </header>

      <Chat userId={USER_ID} />
    </div>
  )
}
