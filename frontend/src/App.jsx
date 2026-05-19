import { useEffect, useState } from 'react'

const API = 'http://localhost:8000'

export default function App() {
  const [form, setForm] = useState({ source_title: '', source_type: 'book', note_text: '', tags: '' })
  const [dueCards, setDueCards] = useState([])
  const [revealed, setRevealed] = useState({})

  async function fetchDue() {
    const res = await fetch(`${API}/cards/due`)
    setDueCards(await res.json())
  }

  useEffect(() => {
    fetchDue()
  }, [])

  async function submitNote(e) {
    e.preventDefault()
    await fetch(`${API}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form, tags: form.tags.split(',').map((t) => t.trim()).filter(Boolean) }),
    })
    setForm({ source_title: '', source_type: 'book', note_text: '', tags: '' })
    fetchDue()
  }

  async function rateCard(cardId, rating) {
    await fetch(`${API}/cards/${cardId}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rating }),
    })
    fetchDue()
  }

  return (
    <main style={{ maxWidth: 900, margin: '0 auto', fontFamily: 'sans-serif' }}>
      <h1>Knowledge Retention Quiz Bot (MVP)</h1>

      <form onSubmit={submitNote} style={{ display: 'grid', gap: 8, marginBottom: 24 }}>
        <input placeholder="Source title" value={form.source_title} onChange={(e) => setForm({ ...form, source_title: e.target.value })} required />
        <select value={form.source_type} onChange={(e) => setForm({ ...form, source_type: e.target.value })}>
          <option value="book">Book</option>
          <option value="article">Article</option>
          <option value="pdf">PDF</option>
          <option value="certification">Certification</option>
          <option value="other">Other</option>
        </select>
        <textarea placeholder="Paste notes/highlights" rows="5" value={form.note_text} onChange={(e) => setForm({ ...form, note_text: e.target.value })} required />
        <input placeholder="Tags (comma separated)" value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} />
        <button type="submit">Save note + generate cards</button>
      </form>

      <h2>Due cards</h2>
      {dueCards.length === 0 && <p>No cards due.</p>}
      {dueCards.map((card) => (
        <div key={card.id} style={{ border: '1px solid #ddd', padding: 12, marginBottom: 12 }}>
          <p><strong>Q:</strong> {card.question}</p>
          <button onClick={() => setRevealed({ ...revealed, [card.id]: !revealed[card.id] })}>Reveal answer</button>
          {revealed[card.id] && <p><strong>A:</strong> {card.answer}</p>}
          <div style={{ display: 'flex', gap: 8 }}>
            {['AGAIN', 'HARD', 'GOOD', 'EASY'].map((r) => (
              <button key={r} onClick={() => rateCard(card.id, r)}>{r}</button>
            ))}
          </div>
        </div>
      ))}
    </main>
  )
}
