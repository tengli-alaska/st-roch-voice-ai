# St. Roch Voice AI - Pitch Idea Build

A Retrieval-Augmented Generation (RAG) system for the Vancouver Maritime Museum's St. Roch exhibit. Visitors ask questions about the 1944 Northwest Passage voyage and receive sourced answers grounded in archival materials, with Inuit perspectives surfaced first.

---

## What It Does

- Indexes archival text documents into a searchable vector store
- Retrieves the most relevant passages for any visitor question
- Generates a concise, sourced answer using a language model (Groq)
- Serves a tablet-friendly React frontend via a Flask backend

---

## Project Structure

```
poc_demo/
├── venv/                        # Python virtual environment (not committed)
├── data/
│   ├── raw/                     # Source .txt files (your knowledge base)
│   └── processed/
│       └── rag_store.json       # Generated embeddings (not committed)
├── rag_pipeline.py              # Chunks and embeds raw text files
├── backend.py                   # Flask API + Groq integration
└── frontend/                    # React app
    └── src/
        ├── App.js
        ├── StRochRAG.jsx
        └── StRochRAG.css
```

---

## Prerequisites

- Python 3.8+
- Node.js 14+
- A [Groq API key](https://console.groq.com) (free)

---

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd poc_demo
```

### 2. Create Python virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Python dependencies

```bash
pip install flask flask-cors sentence-transformers numpy groq
```

### 4. Install React dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Set your Groq API key

```bash
export GROQ_API_KEY="gsk_your_key_here"
```

On Windows (PowerShell):
```powershell
$env:GROQ_API_KEY = "gsk_your_key_here"
```

---

## Running the App

### Step 1: Add data

Place `.txt` files in `data/raw/`. Each file becomes part of the knowledge base. Filename conventions:

- `interview_*` or `inuit_*` → tagged as Inuit perspective (weighted higher in retrieval)
- `crew_*` or `log_*` → tagged as crew perspective
- anything else → tagged as external/historical

### Step 2: Build the RAG store

```bash
source venv/bin/activate
python3 rag_pipeline.py
```

This reads all `.txt` files in `data/raw/`, chunks them, embeds them with Sentence-BERT, and writes `data/processed/rag_store.json`.

Re-run this any time you add or update data files.

### Step 3: Start the backend

```bash
python3 backend.py
```

Backend runs at `http://localhost:5000`

### Step 4: Start the frontend

In a new terminal tab:

```bash
cd frontend
npm start
```

Frontend runs at `http://localhost:3000`

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Check backend status |
| `POST` | `/api/ask` | Ask a question, get an answer |
| `POST` | `/api/retrieve` | Debug: see which chunks were retrieved |

### Example request

```bash
curl -X POST http://localhost:5000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Who was Joe Panipakuttuk?"}'
```

### Example response

```json
{
  "question": "Who was Joe Panipakuttuk?",
  "answer": "Joe Panipakuttuk was an Inuit guide and hunter critical to the 1944 voyage...",
  "sources": ["st_roch_1944"],
  "confidence": 0.57
}
```

---

## Adding More Data

The system gets better with more source material. To add a new source:

1. Save the text content as a `.txt` file in `data/raw/`
2. Name it descriptively (e.g., `interview_joe_panipakuttuk.txt`)
3. Re-run `python3 rag_pipeline.py`
4. Restart `python3 backend.py`

Recommended sources to add:

- QTC Truth Commission interview transcripts: https://www.qtcommission.ca/en/interview-videos
- VMM 2000s digitized interview transcripts (request from museum)
- Crew logs from the 1944 voyage (request digitized copies from museum)

---

## How the RAG System Works

```
Raw text files
    ↓
Split into 300-character overlapping chunks
    ↓
Embed each chunk with Sentence-BERT (all-MiniLM-L6-v2, runs locally)
    ↓
Store vectors in rag_store.json
    ↓
At query time: embed the question, find top-5 closest chunks
    ↓
Pass chunks as context to Groq (Llama 3.1)
    ↓
Return 2-3 sentence answer with source citations
```

Inuit perspective chunks are weighted 1.5x in retrieval so they surface first regardless of query wording.

---

## Confidence Score

The confidence score shown in the UI is the cosine similarity between the query embedding and the best-matching chunk. It reflects retrieval quality, not answer correctness.

- `0.7+` — strong match, reliable retrieval
- `0.5–0.7` — moderate match
- `< 0.5` — weak match, answer may be incomplete

Adding more data files raises scores significantly.

---

## Cultural Guidelines

This system surfaces Inuit perspectives on the 1944 voyage. When adding content, follow these principles:

- Use authentic archival sources — do not fabricate or synthesize Inuit voices
- Credit Inuit contributors by name (Joe Panipakuttuk, Letia, Aariak, Panikpak)
- Frame Inuit knowledge as essential to the voyage, not supplementary
- For interview content, confirm licensing with the museum before use

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | Your Groq API key from console.groq.com |

---

## .gitignore

Make sure your `.gitignore` includes:

```
venv/
data/processed/
__pycache__/
*.pyc
.env
frontend/node_modules/
frontend/build/
```

---

## Troubleshooting

**`source: no such file or directory: venv/bin/activate`**
The venv was not created yet. Run `python3 -m venv venv` first, then activate.

**`ModuleNotFoundError`**
Make sure the venv is active (`source venv/bin/activate`) before running any Python files.

**Frontend can't reach backend**
Make sure `python3 backend.py` is running in a separate terminal. Check that `BACKEND` in `StRochRAG.jsx` points to `http://localhost:5000`.

**Low confidence scores**
Add more `.txt` files to `data/raw/` and rerun `python3 rag_pipeline.py`. More data = better retrieval.

**Groq API errors**
Verify your key is set: `echo $GROQ_API_KEY`. If it's empty, re-run the export command.

---