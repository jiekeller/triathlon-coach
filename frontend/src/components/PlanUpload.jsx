import { useState } from 'react'

export default function PlanUpload({ userId, onUploaded }) {
  const [open, setOpen] = useState(false)
  const [file, setFile] = useState(null)
  const [raceDate, setRaceDate] = useState('')
  const [raceType, setRaceType] = useState('olympic')
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('')

  async function handleUpload(e) {
    e.preventDefault()
    if (!file || !raceDate) return

    setLoading(true)
    setStatus('')
    const form = new FormData()
    form.append('file', file)
    form.append('user_id', userId)
    form.append('race_date', raceDate)
    form.append('race_type', raceType)

    try {
      const res = await fetch('/api/upload-plan', { method: 'POST', body: form })
      const data = await res.json()
      if (data.saved) {
        setStatus(`✓ Plan uploaded (${data.characters.toLocaleString()} characters extracted)`)
        onUploaded?.()
        setTimeout(() => setOpen(false), 1500)
      } else {
        setStatus(`Error: ${data.error}`)
      }
    } catch {
      setStatus('Upload failed — is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        style={{
          background: 'none',
          border: '1px solid #2a2d3a',
          color: '#9ca3af',
          borderRadius: 8,
          padding: '6px 12px',
          fontSize: 13,
          cursor: 'pointer',
        }}
      >
        📄 Upload training plan
      </button>

      {open && (
        <div style={{
          position: 'fixed', inset: 0,
          background: 'rgba(0,0,0,0.7)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 100,
        }}
          onClick={e => e.target === e.currentTarget && setOpen(false)}
        >
          <div style={{
            background: '#1a1d27',
            border: '1px solid #2a2d3a',
            borderRadius: 14,
            padding: 28,
            width: 420,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}>
            <h2 style={{ fontSize: 17, fontWeight: 600 }}>Upload Training Plan PDF</h2>

            <form onSubmit={handleUpload} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ fontSize: 13, color: '#9ca3af', display: 'block', marginBottom: 6 }}>
                  PDF file
                </label>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={e => setFile(e.target.files[0])}
                  required
                  style={{ color: '#e8eaf0', width: '100%' }}
                />
              </div>

              <div>
                <label style={{ fontSize: 13, color: '#9ca3af', display: 'block', marginBottom: 6 }}>
                  Race type
                </label>
                <select
                  value={raceType}
                  onChange={e => setRaceType(e.target.value)}
                  style={{
                    width: '100%', padding: '8px 10px',
                    background: '#0f1117', border: '1px solid #2a2d3a',
                    borderRadius: 8, color: '#e8eaf0', fontSize: 14,
                  }}
                >
                  <option value="sprint">Sprint</option>
                  <option value="olympic">Olympic</option>
                  <option value="70.3">70.3 (Half Ironman)</option>
                  <option value="ironman">Ironman</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: 13, color: '#9ca3af', display: 'block', marginBottom: 6 }}>
                  Race date
                </label>
                <input
                  type="date"
                  value={raceDate}
                  onChange={e => setRaceDate(e.target.value)}
                  required
                  style={{
                    width: '100%', padding: '8px 10px',
                    background: '#0f1117', border: '1px solid #2a2d3a',
                    borderRadius: 8, color: '#e8eaf0', fontSize: 14,
                  }}
                />
              </div>

              {status && (
                <p style={{ fontSize: 13, color: status.startsWith('✓') ? '#4ade80' : '#f87171' }}>
                  {status}
                </p>
              )}

              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                <button type="button" onClick={() => setOpen(false)} style={{
                  background: 'none', border: '1px solid #2a2d3a',
                  color: '#9ca3af', borderRadius: 8, padding: '8px 16px', cursor: 'pointer',
                }}>
                  Cancel
                </button>
                <button type="submit" disabled={loading} style={{
                  background: loading ? '#2a2d3a' : '#3b82f6',
                  color: loading ? '#6b7280' : '#fff',
                  border: 'none', borderRadius: 8,
                  padding: '8px 18px', fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
                }}>
                  {loading ? 'Uploading…' : 'Upload'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}
