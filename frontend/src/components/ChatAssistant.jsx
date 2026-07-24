import React, { useRef, useState, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { applyAiResult, applyChatFieldUpdate } from '../store/complaintSlice'
import {
  messageSent, messageReceived, extractionStarted, extractionProgress,
  extractionFinished, thinkingStarted, thinkingFinished, pastedTextChanged,
} from '../store/chatSlice'
import { api } from '../api/client'
import { UploadCloud, FileText, Send, Sparkles, ListChecks, ShieldAlert } from 'lucide-react'

const ACCEPTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.eml']

function useFakeProgress(active, dispatch) {
  useEffect(() => {
    if (!active) return
    let pct = 8
    const id = setInterval(() => {
      pct = Math.min(pct + Math.random() * 12, 92)
      dispatch(extractionProgress(Math.round(pct)))
    }, 350)
    return () => clearInterval(id)
  }, [active, dispatch])
}

export default function ChatAssistant() {
  const dispatch = useDispatch()
  const { messages, progress, isExtracting, isThinking, pastedText } = useSelector((s) => s.chat)
  const complaintFields = useSelector((s) => s.complaint.fields)
  const [dragOver, setDragOver] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const fileInputRef = useRef(null)
  const scrollRef = useRef(null)

  useFakeProgress(isExtracting, dispatch)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, isThinking])

  const runExtraction = async (kind, payload) => {
    dispatch(extractionStarted())
    try {
      const result = kind === 'file'
        ? await api.extractFromFile(payload, complaintFields)
        : await api.extractFromText(payload, complaintFields)
      dispatch(extractionFinished())
      dispatch(applyAiResult(result))
      dispatch(messageReceived(result.assistant_message))
    } catch (e) {
      dispatch(extractionFinished())
      dispatch(messageReceived(`I ran into an issue analyzing that: ${e.message}. You can also fill the form manually.`))
    }
  }

  const handleFile = (file) => {
    if (!file) return
    dispatch(messageSent(`📎 Uploaded: ${file.name}`))
    runExtraction('file', file)
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    handleFile(e.dataTransfer.files?.[0])
  }

  const onPasteSubmit = () => {
    if (!pastedText.trim()) return
    dispatch(messageSent(pastedText))
    runExtraction('text', pastedText)
    dispatch(pastedTextChanged(''))
  }

  const onChatSend = async () => {
    const msg = chatInput.trim()
    if (!msg) return
    dispatch(messageSent(msg))
    setChatInput('')
    dispatch(thinkingStarted())
    try {
      const history = messages.slice(-8)
      const result = await api.chat(msg, complaintFields, history)
      dispatch(applyChatFieldUpdate(result))
      dispatch(messageReceived(result.assistant_message))
    } catch (e) {
      dispatch(messageReceived(`Sorry, I couldn't process that: ${e.message}`))
    } finally {
      dispatch(thinkingFinished())
    }
  }

  const complaint = useSelector((s) => s.complaint)
  const hasInsights = complaint.summary || complaint.rootCauseSuggestion || complaint.capaSuggestion

  return (
    <section className="panel chat-panel">
      <div className="panel__header">
        <div className="chat-panel__title-row">
          <Sparkles size={17} className="chat-panel__title-icon" />
          <h2 className="panel__title panel__title--sm">AI Complaint Intake Assistant</h2>
        </div>
        <span className="badge badge--beta">BETA</span>
      </div>

      <div
        className={`dropzone${dragOver ? ' dropzone--active' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <UploadCloud size={22} />
        <div>
          <div className="dropzone__title">Drag &amp; drop complaint document here</div>
          <div className="dropzone__subtitle">or click to browse</div>
        </div>
        <input
          type="file"
          ref={fileInputRef}
          accept={ACCEPTED_EXTENSIONS.join(',')}
          style={{ display: 'none' }}
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>

      <div className="divider"><span>OR</span></div>

      <div className="paste-box">
        <textarea
          className="paste-box__input"
          placeholder="Paste complaint text / email..."
          value={pastedText}
          onChange={(e) => dispatch(pastedTextChanged(e.target.value))}
          rows={2}
        />
        <button className="btn btn--secondary btn--block" onClick={onPasteSubmit} disabled={isExtracting}>
          <FileText size={14} /> Analyze Pasted Text
        </button>
      </div>

      <div className="format-note">
        Supported formats: PDF, DOCX, TXT, EML &middot; Max file size: 10MB
      </div>

      {isExtracting && (
        <div className="progress-block">
          <div className="progress-block__label">
            <span>EXTRACTION PROGRESS</span>
            <span>{progress}%</span>
          </div>
          <div className="progress-bar">
            <div className="progress-bar__fill" style={{ width: `${progress}%` }} />
          </div>
          <div className="progress-block__hint">Analyzing document content and extracting key details. Please wait, this may take a few moments.</div>
        </div>
      )}

      <div className="chat-thread" ref={scrollRef}>
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble chat-bubble--${m.role}`}>
            {m.role === 'assistant' && <Sparkles size={13} className="chat-bubble__icon" />}
            <span>{m.content}</span>
          </div>
        ))}
        {isThinking && (
          <div className="chat-bubble chat-bubble--assistant chat-bubble--thinking">
            <Sparkles size={13} className="chat-bubble__icon" />
            <span className="typing-dots"><i /><i /><i /></span>
          </div>
        )}

        {hasInsights && (
          <div className="ai-insights">
            {complaint.summary && (
              <div className="ai-insights__item">
                <div className="ai-insights__label"><Sparkles size={12} /> Summary</div>
                <p>{complaint.summary}</p>
              </div>
            )}
            {complaint.nextSteps?.length > 0 && (
              <div className="ai-insights__item">
                <div className="ai-insights__label"><ListChecks size={12} /> Recommended Next Steps</div>
                <ul>{complaint.nextSteps.map((s, i) => <li key={i}>{s}</li>)}</ul>
              </div>
            )}
            {complaint.precautions?.length > 0 && (
              <div className="ai-insights__item">
                <div className="ai-insights__label"><ShieldAlert size={12} /> Immediate Precautions</div>
                <ul>{complaint.precautions.map((s, i) => <li key={i}>{s}</li>)}</ul>
              </div>
            )}
            {complaint.rootCauseSuggestion && (
              <div className="ai-insights__item">
                <div className="ai-insights__label">Root Cause Suggestion</div>
                <p>{complaint.rootCauseSuggestion}</p>
              </div>
            )}
            {complaint.capaSuggestion && (
              <div className="ai-insights__item">
                <div className="ai-insights__label">CAPA Suggestion</div>
                <p>{complaint.capaSuggestion}</p>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="chat-input-row">
        <input
          type="text"
          placeholder="Ask me anything about this complaint..."
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && onChatSend()}
        />
        <button className="chat-send-btn" onClick={onChatSend} aria-label="Send">
          <Send size={16} />
        </button>
      </div>
      <div className="disclaimer">AI responses may contain errors. Please verify information.</div>
    </section>
  )
}
