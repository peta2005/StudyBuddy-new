import os


import logging
import pickle
import numpy as np
import faiss

logger = logging.getLogger(__name__)
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        logger.info("Loading SentenceTransformer model (lazy)...")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def create_vector_store(pages, store_dir="vector_store"):
    os.makedirs(store_dir, exist_ok=True)

    texts = [p["text"] for p in pages]
    embeddings = get_embedding_model().encode(texts, show_progress_bar=False)

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings).astype('float32'))

    faiss.write_index(index, os.path.join(store_dir, "faiss.index"))
    with open(os.path.join(store_dir, "metadata.pkl"), "wb") as f:
        pickle.dump(pages, f)

    logger.info("Vector store created with %d pages.", len(pages))
