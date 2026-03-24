import { useState, useEffect } from 'react'

const ACCEPT = '.pdf,.jpg,.jpeg,.png,.gif,.webp,.txt'

export default function FileUpload({ userId }) {
  const [open, setOpen] = useState(false)
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [status, setStatus] = useState('')

  useEffect(() => {
    if (open) fetchFiles()
  }, [open])

  async function fetchFiles() {
    const res = await fetch(`/api/files/${userId}`)
    const data = await res.json()
    setFiles(data.files || [])
  }

  async function handleUpload(e) {
    const file = e.target.files[0]
    if (!file) return

    setUploading(true)
    setStatus('')
    const form = new FormData()
    form.append('file', file)
    form.append('user_id', userId)

    try {
      const res = await fetch('/api/upload-file', { method: 'POST', body: form })
      const data = await res.json()
      if (data.saved) {
        setStatus(`✓ "${file.name}" uploaded`)
        fetchFiles()
      } else {
        setStatus(`Error: ${data.error}`)
      }
    } catch {
      setStatus('Upload failed — is the backend running?')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  async function handleDelete(fileId, filename) {
    if (!confirm(`Delete "${filename}"?`)) return
    await fetch(`/api/files/${fileId}?user_id=${userId}`, { method: 'DELETE' })
    fetchFiles()
  }

  function fileIcon(mimeType) {
    if (mimeType.startsWith('image/')) return '🖼️'
    if (mimeType === 'application/pdf') return '📄'
    return '📝'
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
        📎 Files {files.length > 0 && `(${files.length})`}
      </button>

      {open && (
        <div
          style={{
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
            width: 460,
            display: 'flex',
            flexDirection: 'column',
            gap: 18,
            maxHeight: '80vh',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ fontSize: 17, fontWeight: 600 }}>Your Files</h2>
              <button onClick={() => setOpen(false)} style={{
                background: 'none', border: 'none', color: '#6b7280',
                fontSize: 20, cursor: 'pointer', lineHeight: 1,
              }}>×</button>
            </div>

            <p style={{ fontSize: 13, color: '#6b7280', marginTop: -10 }}>
              Upload screenshots, race results, PDFs, or any reference files. Claude will see them in your conversation.
            </p>

            {/* Upload button */}
            <label style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              border: '2px dashed #2a2d3a', borderRadius: 10,
              padding: '14px 20px', cursor: 'pointer',
              color: uploading ? '#6b7280' : '#9ca3af',
              fontSize: 14, transition: 'border-color 0.15s',
            }}
              onMouseEnter={e => e.currentTarget.style.borderColor = '#3b82f6'}
              onMouseLeave={e => e.currentTarget.style.borderColor = '#2a2d3a'}
            >
              <input
                type="file"
                accept={ACCEPT}
                onChange={handleUpload}
                disabled={uploading}
                style={{ display: 'none' }}
              />
              {uploading ? '⏳ Uploading…' : '＋ Click to upload a file'}
            </label>

            <p style={{ fontSize: 12, color: '#6b7280', marginTop: -10, textAlign: 'center' }}>
              PDF, PNG, JPG, GIF, WEBP, TXT
            </p>

            {status && (
              <p style={{ fontSize: 13, color: status.startsWith('✓') ? '#4ade80' : '#f87171', textAlign: 'center' }}>
                {status}
              </p>
            )}

            {/* File list */}
            <div style={{ overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
              {files.length === 0 ? (
                <p style={{ color: '#6b7280', fontSize: 13, textAlign: 'center', padding: '12px 0' }}>
                  No files uploaded yet
                </p>
              ) : (
                files.map(f => (
                  <div key={f.id} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    background: '#0f1117', borderRadius: 8, padding: '8px 12px',
                    border: '1px solid #2a2d3a',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
                      <span style={{ fontSize: 18, flexShrink: 0 }}>{fileIcon(f.mime_type)}</span>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontSize: 13, color: '#e8eaf0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {f.filename}
                        </div>
                        <div style={{ fontSize: 11, color: '#6b7280' }}>
                          {new Date(f.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDelete(f.id, f.filename)}
                      title="Delete"
                      style={{
                        background: 'none', border: 'none', color: '#6b7280',
                        cursor: 'pointer', fontSize: 16, flexShrink: 0, padding: '2px 6px',
                      }}
                    >
                      🗑
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
