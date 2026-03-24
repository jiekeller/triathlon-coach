import { useState, useRef, useEffect } from 'react'
import Message from './Message.jsx'

const WELCOME = {
  role: 'assistant',
  content: "Hey! I'm your triathlon coach 👋\n\nI can help you with:\n- **Reviewing your training** against your plan\n- **Generating a training plan** for your next race\n- **Nutrition advice** and weekly grocery lists\n- **Adjusting your week** if you miss sessions\n\nTo get started, tell me about your next race — what distance and when is it? Or connect your Strava and ask me how your training is going.",
}

export default function Chat({ userId }) {
  const [messages, setMessages] = useState([WELCOME])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send() {
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, message: text }),
      })
      const data = await res.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply }])
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '⚠️ Something went wrong. Is the backend running?',
      }])
    } finally {
      setLoading(false)
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  async function clearChat() {
    await fetch(`/api/chat/${userId}`, { method: 'DELETE' })
    setMessages([WELCOME])
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      {/* Messages */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
      }}>
        {messages.map((m, i) => <Message key={i} message={m} />)}

        {loading && (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', color: '#6b7280' }}>
            <div style={{ display: 'flex', gap: 4 }}>
              {[0, 1, 2].map(i => (
                <span key={i} style={{
                  width: 6, height: 6, borderRadius: '50%',
                  background: '#6b7280',
                  animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite`,
                }} />
              ))}
            </div>
            <span style={{ fontSize: 13 }}>Coach is thinking…</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div style={{
        borderTop: '1px solid #2a2d3a',
        padding: '12px 16px',
        background: '#1a1d27',
        display: 'flex',
        gap: 8,
        alignItems: 'flex-end',
        flexShrink: 0,
      }}>
        <button
          onClick={clearChat}
          title="Clear chat history"
          style={{
            background: 'none',
            border: '1px solid #2a2d3a',
            color: '#6b7280',
            borderRadius: 8,
            padding: '8px 10px',
            cursor: 'pointer',
            fontSize: 16,
            flexShrink: 0,
          }}
        >
          🗑
        </button>

        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask your coach anything… (Enter to send, Shift+Enter for new line)"
          rows={1}
          style={{
            flex: 1,
            background: '#0f1117',
            border: '1px solid #2a2d3a',
            borderRadius: 10,
            color: '#e8eaf0',
            padding: '10px 14px',
            fontSize: 15,
            resize: 'none',
            outline: 'none',
            lineHeight: 1.5,
            maxHeight: 120,
            overflowY: 'auto',
          }}
        />

        <button
          onClick={send}
          disabled={loading || !input.trim()}
          style={{
            background: loading || !input.trim() ? '#2a2d3a' : '#3b82f6',
            color: loading || !input.trim() ? '#6b7280' : '#fff',
            border: 'none',
            borderRadius: 10,
            padding: '10px 18px',
            fontWeight: 600,
            fontSize: 15,
            cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
            flexShrink: 0,
            transition: 'background 0.15s',
          }}
        >
          Send
        </button>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.3; transform: scale(0.8); }
          50% { opacity: 1; transform: scale(1.2); }
        }
      `}</style>
    </div>
  )
}
