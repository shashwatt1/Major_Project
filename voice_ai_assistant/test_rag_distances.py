import sys
sys.path.insert(0, 'backend')
from modules.rag import retrieve, _get_embedder, _get_index
import numpy as np

query = "what is the capital of uttarakhand?"
index, chunks, sources = _get_index()
embedder = _get_embedder()

query_embedding = embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True)
query_embedding = np.asarray(query_embedding, dtype="float32")

limit = min(3, len(chunks))
distances, indices = index.search(query_embedding, limit)

print("Distances:", distances[0])
print("Indices:", indices[0])

for dist, idx in zip(distances[0], indices[0]):
    print(f"Dist: {dist:.4f}, Source: {sources[idx]}, Content: {chunks[idx][:50]}...")
