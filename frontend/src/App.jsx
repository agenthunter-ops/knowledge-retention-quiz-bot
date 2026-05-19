import { useEffect, useMemo, useState } from 'react'
import './App.css'

const API = 'http://localhost:8000'

const pages = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'add-highlight', label: 'Add Highlight' },
  { key: 'due-cards', label: 'Due Cards' },
  { key: 'card-management', label: 'Card Management' },
]

export default function App() {
  const [activePage, setActivePage] = useState('dashboard')
  const [highlights, setHighlights] = useState([])
  const [cards, setCards] = useState([])
  const [dueCards, setDueCards] = useState([])
  const [revealed, setRevealed] = useState({})
  const [lastReviewUpdate, setLastReviewUpdate] = useState({})
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')

  const [highlightForm, setHighlightForm] = useState({
    source_title: '',
    source_type: 'book',
    text: '',
    tags: '',
  })

  const [editingCardId, setEditingCardId] = useState(null)
  const [editForm, setEditForm] = useState({ question: '', answer: '' })

  const stats = useMemo(() => {
    const dueToday = dueCards.length
    const flaggedCards = cards.filter((c) => c.is_flagged).length
    return {
      totalHighlights: highlights.length,
      totalCards: cards.length,
      dueToday,
      flaggedCards,
    }
  }, [highlights, cards, dueCards])

  async function loadData() {
    setLoading(true)
    try {
      const [highlightsRes, cardsRes, dueCardsRes] = await Promise.all([
        fetch(`${API}/highlights`),
        fetch(`${API}/cards`),
        fetch(`${API}/cards/due`),
      ])

      const [highlightsData, cardsData, dueCardsData] = await Promise.all([
        highlightsRes.json(),
        cardsRes.json(),
        dueCardsRes.json(),
      ])

      setHighlights(highlightsData)
      setCards(cardsData)
      setDueCards(dueCardsData)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  async function submitHighlight(e) {
    e.preventDefault()
    setSubmitting(true)
    setSubmitError('')
    try {
      const res = await fetch(`${API}/highlights`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...highlightForm,
          tags: highlightForm.tags
            .split(',')
            .map((t) => t.trim())
            .filter(Boolean),
        }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        const detail = err.detail
        const message = Array.isArray(detail)
          ? detail.map((d) => d.msg).join(', ')
          : typeof detail === 'string'
            ? detail
            : `Request failed (${res.status})`
        throw new Error(message)
      }

      setHighlightForm({ source_title: '', source_type: 'book', text: '', tags: '' })
      setActivePage('due-cards')
      await loadData()
    } catch (err) {
      setSubmitError(
        err.message || 'Failed to submit highlight. Make sure the backend is running on http://localhost:8000.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  async function rateCard(cardId, rating) {
    const res = await fetch(`${API}/reviews/${cardId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rating }),
    })
    const updatedCard = await res.json()
    setLastReviewUpdate((prev) => ({ ...prev, [cardId]: updatedCard.due_date }))
    loadData()
  }

  function startEdit(card) {
    setEditingCardId(card.id)
    setEditForm({ question: card.question, answer: card.answer })
  }

  async function saveCardEdit(cardId) {
    await fetch(`${API}/cards/${cardId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editForm),
    })
    setEditingCardId(null)
    loadData()
  }

  async function flagCard(cardId) {
    await fetch(`${API}/cards/${cardId}/flag`, { method: 'POST' })
    loadData()
  }

  return (
    <main className="app-shell">
      <header className="header">
        <h1>Knowledge Retention Quiz Bot</h1>
        <p>Simple MVP interface for highlights and spaced-repetition cards.</p>
      </header>

      <nav className="tabs">
        {pages.map((page) => (
          <button
            key={page.key}
            className={activePage === page.key ? 'tab active' : 'tab'}
            onClick={() => setActivePage(page.key)}
          >
            {page.label}
          </button>
        ))}
      </nav>

      {loading && <p className="muted">Loading...</p>}

      {activePage === 'dashboard' && (
        <section className="card-grid">
          <StatCard label="Total Highlights" value={stats.totalHighlights} />
          <StatCard label="Total Cards" value={stats.totalCards} />
          <StatCard label="Due Today" value={stats.dueToday} />
          <StatCard label="Flagged Cards" value={stats.flaggedCards} />
        </section>
      )}

      {activePage === 'add-highlight' && (
        <section className="panel">
          <h2>Add Highlight</h2>
          <form onSubmit={submitHighlight} className="form-grid">
            <label>
              Source Title
              <input
                value={highlightForm.source_title}
                onChange={(e) => setHighlightForm({ ...highlightForm, source_title: e.target.value })}
                required
              />
            </label>

            <label>
              Source Type
              <select
                value={highlightForm.source_type}
                onChange={(e) => setHighlightForm({ ...highlightForm, source_type: e.target.value })}
              >
                <option value="book">Book</option>
                <option value="article">Article</option>
                <option value="pdf">PDF</option>
                <option value="certification">Certification</option>
                <option value="other">Other</option>
              </select>
            </label>

            <label>
              Tags
              <input
                placeholder="comma, separated, tags"
                value={highlightForm.tags}
                onChange={(e) => setHighlightForm({ ...highlightForm, tags: e.target.value })}
              />
            </label>

            <label>
              Note / Highlight Text
              <textarea
                rows="5"
                value={highlightForm.text}
                onChange={(e) => setHighlightForm({ ...highlightForm, text: e.target.value })}
                required
              />
            </label>

            {submitError && <p className="error">{submitError}</p>}
            <button type="submit" className="primary-btn" disabled={submitting}>
              {submitting ? 'Generating cards…' : 'Submit Highlight'}
            </button>
          </form>
        </section>
      )}

      {activePage === 'due-cards' && (
        <section className="panel">
          <h2>Due Cards</h2>
          {dueCards.length === 0 ? (
            <p className="muted">No cards due right now.</p>
          ) : (
            dueCards.map((card) => (
              <article key={card.id} className="quiz-card">
                <p><strong>Question:</strong> {card.question}</p>
                <button className="secondary-btn" onClick={() => setRevealed((prev) => ({ ...prev, [card.id]: !prev[card.id] }))}>
                  {revealed[card.id] ? 'Hide Answer' : 'Reveal Answer'}
                </button>

                {revealed[card.id] && <p><strong>Answer:</strong> {card.answer}</p>}

                <div className="rating-row">
                  {['AGAIN', 'HARD', 'GOOD', 'EASY'].map((rating) => (
                    <button key={rating} className="rating-btn" onClick={() => rateCard(card.id, rating)}>{rating}</button>
                  ))}
                </div>

                {lastReviewUpdate[card.id] && (
                  <p className="muted">Next due date: {new Date(lastReviewUpdate[card.id]).toLocaleString()}</p>
                )}
              </article>
            ))
          )}
        </section>
      )}

      {activePage === 'card-management' && (
        <section className="panel">
          <h2>Card Management</h2>
          {cards.length === 0 ? (
            <p className="muted">No cards available yet.</p>
          ) : (
            cards.map((card) => (
              <article key={card.id} className="manage-card">
                {editingCardId === card.id ? (
                  <>
                    <label>
                      Question
                      <input value={editForm.question} onChange={(e) => setEditForm({ ...editForm, question: e.target.value })} />
                    </label>
                    <label>
                      Answer
                      <textarea rows="3" value={editForm.answer} onChange={(e) => setEditForm({ ...editForm, answer: e.target.value })} />
                    </label>
                    <div className="action-row">
                      <button className="primary-btn" onClick={() => saveCardEdit(card.id)}>Save</button>
                      <button className="secondary-btn" onClick={() => setEditingCardId(null)}>Cancel</button>
                    </div>
                  </>
                ) : (
                  <>
                    <p><strong>Q:</strong> {card.question}</p>
                    <p><strong>A:</strong> {card.answer}</p>
                    <p><strong>Card Type:</strong> {card.card_type}</p>
                    <p><strong>Difficulty:</strong> {card.difficulty}</p>
                    <p><strong>Explanation:</strong> {card.explanation}</p>
                    <p><strong>Why it matters:</strong> {card.why_it_matters}</p>
                    <p><strong>Source Quote:</strong> {card.source_quote}</p>
                    <p className="muted">Status: {card.is_flagged ? 'Flagged' : 'Active'}</p>
                    <div className="action-row">
                      <button className="secondary-btn" onClick={() => startEdit(card)}>Edit</button>
                      <button className="danger-btn" onClick={() => flagCard(card.id)} disabled={card.is_flagged}>
                        {card.is_flagged ? 'Flagged' : 'Flag Bad Card'}
                      </button>
                    </div>
                  </>
                )}
              </article>
            ))
          )}
        </section>
      )}
    </main>
  )
}

function StatCard({ label, value }) {
  return (
    <article className="stat-card">
      <p className="muted">{label}</p>
      <h3>{value}</h3>
    </article>
  )
}
