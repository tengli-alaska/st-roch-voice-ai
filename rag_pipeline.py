import json
import os
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

RAW_DIR = Path('./data/raw')
OUTPUT_PATH = Path('./data/processed/rag_store.json')
MODEL_NAME = 'all-MiniLM-L6-v2'
CHUNK_SIZE = 300
OVERLAP = 50

def load_documents():
    docs = {}
    for filepath in RAW_DIR.glob('*.txt'):
        with open(filepath, 'r', encoding='utf-8') as f:
            docs[filepath.stem] = f.read()
    print(f"Loaded {len(docs)} documents")
    return docs

def chunk_text(text):
    chunks = []
    for i in range(0, len(text), CHUNK_SIZE - OVERLAP):
        chunk = text[i:i + CHUNK_SIZE].strip()
        if len(chunk) > 80:
            chunks.append(chunk)
    return chunks

def infer_metadata(doc_name):
    if 'interview' in doc_name.lower() or 'inuit' in doc_name.lower() or 'qtc' in doc_name.lower():
        return 'inuit', ['oral-history', 'inuit-perspective']
    elif 'crew' in doc_name.lower() or 'log' in doc_name.lower():
        return 'crew', ['expedition', '1944-voyage']
    else:
        return 'external', ['historical-context', '1944-voyage']

def build_rag_store():
    print("Loading model...")
    model = SentenceTransformer(MODEL_NAME)

    documents = load_documents()
    all_chunks = []

    for doc_name, doc_text in documents.items():
        perspective, themes = infer_metadata(doc_name)
        text_chunks = chunk_text(doc_text)
        print(f"  {doc_name}: {len(text_chunks)} chunks ({perspective})")

        for i, chunk in enumerate(text_chunks):
            all_chunks.append({
                'chunk_id': f'{doc_name}_{i:03d}',
                'text': chunk,
                'source': doc_name,
                'perspective': perspective,
                'themes': themes,
            })

    print(f"\nEmbedding {len(all_chunks)} chunks...")
    texts = [c['text'] for c in all_chunks]
    embeddings = model.encode(texts, show_progress_bar=True)

    for i, chunk in enumerate(all_chunks):
        chunk['embedding'] = embeddings[i].tolist()

    with open(OUTPUT_PATH, 'w') as f:
        json.dump(all_chunks, f)

    size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    print(f"\nSaved {len(all_chunks)} chunks to {OUTPUT_PATH} ({size_mb:.1f} MB)")
    print("Done!")

if __name__ == '__main__':
    build_rag_store()
