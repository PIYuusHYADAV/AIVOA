import React from 'react'
import ComplaintForm from './components/ComplaintForm'
import ChatAssistant from './components/ChatAssistant'

export default function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header__brand">
          <div className="app-header__mark">AV</div>
          <div>
            <div className="app-header__title">AIVOA</div>
            <div className="app-header__subtitle">Customer Complaint Management System</div>
          </div>
        </div>
        <div className="app-header__meta">Pharmaceutical Manufacturing &middot; QMS Module</div>
      </header>

      <main className="app-grid">
        <ComplaintForm />
        <ChatAssistant />
      </main>
    </div>
  )
}
