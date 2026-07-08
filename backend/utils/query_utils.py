import os
import pickle
import numpy as np
import faiss
from utils.embedding_utils import get_embedding_model

def query_vector_db(query, k=3, store_dir="vector_store"):
    index_path = os.path.join(store_dir, "faiss.index")
    metadata_path = os.path.join(store_dir, "metadata.pkl")

    # Check if vector store exists
    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        return []

    # Load FAISS index and metadata
    index = faiss.read_index(index_path)
    with open(metadata_path, "rb") as f:
        pages = pickle.load(f)

    # Convert query to embedding
    query_embedding = get_embedding_model().encode([query]).astype('float32')

    # Search
    distances, indices = index.search(query_embedding, k)

    passages = []
    for idx in indices[0]:
        if idx < len(pages):
            passages.append({
                "text": pages[idx]["text"],
                "page": pages[idx]["page"]
            })

    return passages