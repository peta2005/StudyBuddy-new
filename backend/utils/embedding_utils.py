import os
import logging
import pickle
import numpy as np
import faiss
import requests

logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
API_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{MODEL_ID}"

def get_embeddings(texts: list[str]) -> np.ndarray:
    """Generate embeddings using Hugging Face Inference API to save server memory."""
    headers = {}
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"
    
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": texts}, timeout=25)
        if response.status_code == 200:
            embeddings = response.json()
            return np.array(embeddings).astype("float32")
        else:
            logger.error("Hugging Face API failed: %s - %s", response.status_code, response.text)
            raise ValueError(f"Hugging Face API failed: {response.text}")
    except Exception as exc:
        logger.exception("Failed to get embeddings from Hugging Face: %s", exc)
        raise


def create_vector_store(pages, store_dir="vector_store"):
    os.makedirs(store_dir, exist_ok=True)

    texts = [p["text"] for p in pages]
    embeddings = get_embeddings(texts)

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, os.path.join(store_dir, "faiss.index"))
    with open(os.path.join(store_dir, "metadata.pkl"), "wb") as f:
        pickle.dump(pages, f)

    logger.info("Vector store created with %d pages.", len(pages))
