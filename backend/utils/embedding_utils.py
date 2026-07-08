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
        response = requests.post(API_URL, headers=headers, json={"inputs": texts}, timeout=15)
        if response.status_code == 200:
            raw_embeddings = response.json()
            
            # If the response is a single dictionary or direct error
            if isinstance(raw_embeddings, dict) and "error" in raw_embeddings:
                raise ValueError(f"Hugging Face error: {raw_embeddings['error']}")
                
            pooled_embeddings = []
            
            # Process each text's embedding output individually
            for item in raw_embeddings:
                item_arr = np.array(item)
                
                # If item_arr is 2D (sequence_length, dim), mean-pool to 1D (dim,)
                if len(item_arr.shape) == 2:
                    pooled = np.mean(item_arr, axis=0)
                # If item_arr is 1D (already pooled to dim,), keep it
                elif len(item_arr.shape) == 1:
                    pooled = item_arr
                else:
                    raise ValueError(f"Unexpected item embedding shape: {item_arr.shape}")
                    
                pooled_embeddings.append(pooled)
                
            return np.array(pooled_embeddings).astype("float32")
        else:
            logger.warning("Hugging Face API returned status code %s. Attempting local fallback...", response.status_code)
    except Exception as exc:
        logger.warning("Hugging Face API request failed (e.g. offline or DNS block): %s. Attempting local fallback...", exc)
        
    # Local fallback for local development or API outages
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Using local SentenceTransformer fallback...")
        local_model = SentenceTransformer("all-MiniLM-L6-v2")
        return local_model.encode(texts, show_progress_bar=False).astype("float32")
    except Exception as local_exc:
        logger.exception("Both Hugging Face API and local SentenceTransformer fallback failed: %s", local_exc)
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
