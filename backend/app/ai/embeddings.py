import os
import numpy as np

class EmbeddingEngine:
    _model = None

    @classmethod
    def get_model(cls):
        """
        Lazily loads and caches the SentenceTransformer model.
        Falls back to mock mode if PyTorch/transformers DLL loads fail on host,
        or if running on Render (to prevent Out-Of-Memory kills on free-tier RAM).
        """
        if os.environ.get("RENDER") == "true" or os.environ.get("FORCE_MOCK_EMBEDDING") == "true":
            print("\n[AI Core]: Render environment detected. Bypassing heavy ML models to prevent RAM OOM kills.\n")
            cls._model = "MOCK_FALLBACK"
            return cls._model

        if cls._model is None:
            try:
                # pyrefly: ignore [missing-import]
                from sentence_transformers import SentenceTransformer
                # This will load from cache if downloaded during Docker build
                cls._model = SentenceTransformer('all-MiniLM-L6-v2')
            except (ImportError, OSError, Exception) as e:
                print(f"\n[AI Core Warning]: PyTorch DLL load failed ({str(e)}).")
                print("[AI Core Warning]: Falling back to local hash-based vector matching (CPU native).\n")
                cls._model = "MOCK_FALLBACK"
        return cls._model

    @classmethod
    def get_embedding(cls, text: str) -> list[float]:
        """
        Generates a 384-dimensional vector embedding for the input text.
        Uses hash-based values if in fallback mode.
        """
        if not text or not text.strip():
            return [0.0] * 384 # Return zero vector if empty
        
        model = cls.get_model()
        if model == "MOCK_FALLBACK":
            import hashlib
            # Generate deterministic mock embedding from string hash
            h = hashlib.sha256(text.encode('utf-8')).digest()
            vector = []
            for i in range(384):
                val = h[i % len(h)]
                vector.append(float(val) / 255.0 - 0.5)
            return vector
            
        # Encode returns a numpy array
        embedding = model.encode(text.strip())
        return embedding.tolist()

    @classmethod
    def calculate_similarity(cls, emb1: list[float], emb2: list[float]) -> float:
        """
        Calculates cosine similarity between two vector embeddings.
        Returns a score scaled from 0 to 100.
        """
        if not emb1 or not emb2 or len(emb1) != len(emb2):
            return 0.0
            
        vec1 = np.array(emb1)
        vec2 = np.array(emb2)
        
        dot_product = np.dot(vec1, vec2)
        norm_a = np.linalg.norm(vec1)
        norm_b = np.linalg.norm(vec2)
        
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
            
        similarity = dot_product / (norm_a * norm_b)
        
        # Normalize and clip from -1..1 to 0..1 then convert to percent
        score = float((similarity + 1) / 2 * 100) if similarity < 0 else float(similarity * 100)
        return round(max(0.0, min(100.0, score)), 2)
