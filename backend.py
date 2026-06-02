import json
import os
from pathlib import Path
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
from groq import Groq

app = Flask(__name__)
CORS(app)

RAG_STORE_PATH = Path('./data/processed/rag_store.json')
MODEL_NAME = 'all-MiniLM-L6-v2'

SYSTEM_PROMPT = """You are a museum assistant for the St. Roch exhibit at the Vancouver Maritime Museum.
Answer visitor questions about the 1944 voyage and the Inuit guides who made it possible.

Guidelines:
- Prioritize Inuit perspectives and frame their contributions as essential, not supplementary
- Keep answers to 2-3 sentences, simple and accessible
- Always mention the source of your information
- Do not fabricate quotes or facts outside the provided context
- If context does not contain the answer, say: I do not have that in the archive, but staff can help.
"""

print("Loading embedding model...")
embedding_model = SentenceTransformer(MODEL_NAME)
print("Embedding model loaded.")

print("Loading RAG store...")
with open(RAG_STORE_PATH, 'r') as f:
    rag_store = json.load(f)
print(f"RAG store loaded: {len(rag_store)} chunks.")

groq_client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def retrieve(query, top_k=5):
    query_embedding = embedding_model.encode(query).tolist()
    weights = {'inuit': 1.5, 'crew': 1.0, 'external': 0.8}
    scored = []
    for chunk in rag_store:
        sim = cosine_similarity(query_embedding, chunk['embedding'])
        w = weights.get(chunk.get('perspective', 'external'), 1.0)
        scored.append((chunk, sim * w, sim))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [(chunk, raw_sim) for chunk, _, raw_sim in scored[:top_k]]

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'chunks': len(rag_store),
        'model': MODEL_NAME
    })

@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'error': 'Question required'}), 400

    results = retrieve(question, top_k=5)
    context = "\n\n".join([
        f"[{chunk['perspective']}] {chunk['source']}:\n{chunk['text']}"
        for chunk, _ in results
    ])
    sources = list(dict.fromkeys([chunk['source'] for chunk, _ in results]))
    confidence = results[0][1] if results else 0.0

    prompt = f"Archive context:\n{context}\n\nVisitor question: {question}\n\nAnswer (2-3 sentences):"

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.3,
    )

    return jsonify({
        'question': question,
        'answer': response.choices[0].message.content,
        'sources': sources,
        'confidence': round(min(confidence, 1.0), 2),
    })

@app.route('/api/retrieve', methods=['POST'])
def retrieve_debug():
    question = request.json.get('question', '').strip()
    if not question:
        return jsonify({'error': 'Question required'}), 400
    results = retrieve(question, top_k=5)
    return jsonify({'chunks': [
        {'text': c['text'][:150], 'source': c['source'],
         'perspective': c['perspective'], 'similarity': round(s, 3)}
        for c, s in results
    ]})

if __name__ == '__main__':
    print("\nStarting St. Roch backend at http://localhost:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
