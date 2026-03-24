import ReactMarkdown from 'react-markdown'

export default function Message({ message }) {
  const isUser = message.role === 'user'

  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      gap: 10,
      alignItems: 'flex-start',
    }}>
      {!isUser && (
        <div style={{
          width: 32, height: 32, borderRadius: '50%',
          background: '#1e3a5f',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 16, flexShrink: 0, marginTop: 2,
        }}>
          🏅
        </div>
      )}

      <div style={{
        maxWidth: '72%',
        background: isUser ? '#1e40af' : '#1a1d27',
        border: isUser ? 'none' : '1px solid #2a2d3a',
        borderRadius: isUser ? '18px 18px 4px 18px' : '4px 18px 18px 18px',
        padding: '10px 14px',
        fontSize: 15,
        lineHeight: 1.6,
        color: '#e8eaf0',
      }}>
        {isUser ? (
          <span style={{ whiteSpace: 'pre-wrap' }}>{message.content}</span>
        ) : (
          <div className="markdown">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>

      {isUser && (
        <div style={{
          width: 32, height: 32, borderRadius: '50%',
          background: '#1e3a5f',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 16, flexShrink: 0, marginTop: 2,
        }}>
          🧑
        </div>
      )}

      <style>{`
        .markdown p { margin-bottom: 8px; }
        .markdown p:last-child { margin-bottom: 0; }
        .markdown ul, .markdown ol { padding-left: 20px; margin-bottom: 8px; }
        .markdown li { margin-bottom: 4px; }
        .markdown h1, .markdown h2, .markdown h3 {
          margin: 12px 0 6px; font-weight: 600;
        }
        .markdown h1 { font-size: 1.15em; }
        .markdown h2 { font-size: 1.05em; }
        .markdown h3 { font-size: 1em; }
        .markdown code {
          background: #0f1117; border-radius: 4px;
          padding: 2px 6px; font-size: 0.9em;
        }
        .markdown pre { background: #0f1117; border-radius: 8px; padding: 12px; overflow-x: auto; margin-bottom: 8px; }
        .markdown pre code { padding: 0; background: none; }
        .markdown strong { color: #93c5fd; }
        .markdown a { color: #60a5fa; }
        .markdown hr { border-color: #2a2d3a; margin: 10px 0; }
        .markdown blockquote { border-left: 3px solid #3b82f6; padding-left: 12px; color: #9ca3af; }
      `}</style>
    </div>
  )
}
