import React, { useState, useRef, useEffect } from 'react';
import './StRochRAG.css';

const BACKEND = 'http://localhost:5000';

const SUGGESTIONS = [
  'Who was Joe Panipakuttuk?',
  'What happened in the 1944 voyage?',
  'How did Inuit help the crew?',
  'What is the Northwest Passage?',
  'Who was Captain Henry Larsen?',
  'What is Inuit Qaujimajatuqangit?',
];

export default function StRochRAG() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer]     = useState(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);
  const textareaRef = useRef(null);

  useEffect(() => { textareaRef.current?.focus(); }, []);

  const ask = async (q) => {
    const query = (q || question).trim();
    if (!query) return;

    setLoading(true);
    setError(null);
    setAnswer(null);

    try {
      const res = await fetch(`${BACKEND}/api/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: query }),
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);

      const data = await res.json();
      setAnswer(data);
      setQuestion('');
    } catch (err) {
      setError('Could not reach the server. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && e.ctrlKey) ask();
  };

  const handleSuggestion = (q) => {
    setQuestion(q);
    ask(q);
  };

  return (
    <div className="container">
      <header className="header">
        <h1>🚢 St. Roch Voice Explorer</h1>
        <p>Ask about the 1944 voyage and the Inuit guides who made it possible</p>
      </header>

      <main className="main">
        <div className="card">
          <label htmlFor="q">Your question</label>
          <textarea
            ref={textareaRef}
            id="q"
            rows={3}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKey}
            placeholder="e.g. Who helped the crew navigate the ice?"
            disabled={loading}
          />

          <div className="btn-row">
            <button
              className="btn btn-primary"
              onClick={() => ask()}
              disabled={loading || !question.trim()}
            >
              {loading ? '⏳ Thinking…' : '❓ Ask'}
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => { setQuestion(''); setAnswer(null); setError(null); }}
              disabled={loading}
            >
              Clear
            </button>
          </div>

          <div className="suggestions">
            <p>Try these:</p>
            <div className="pills">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  className="pill"
                  onClick={() => handleSuggestion(s)}
                  disabled={loading}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>

        {error && <div className="error">⚠️ {error}</div>}

        {answer && (
          <div className="answer-card">
            <h2>Answer</h2>
            <p className="answer-text">{answer.answer}</p>
            <div className="meta">
              <strong>Sources:</strong> {answer.sources.join(' · ')}
              <div className="confidence-bar-bg">
                <div
                  className="confidence-bar"
                  style={{ width: `${Math.round(answer.confidence * 100)}%` }}
                />
              </div>
              Confidence: {Math.round(answer.confidence * 100)}%
            </div>
          </div>
        )}
      </main>

      <footer className="footer">
        Vancouver Maritime Museum · St. Roch Exhibit · Data from VMM Archive
      </footer>
    </div>
  );
}
