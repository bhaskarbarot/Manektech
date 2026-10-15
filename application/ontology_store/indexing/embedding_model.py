import hashlib
import math
import os
import re
from abc import ABC, abstractmethod

DEFAULT_ST_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class EmbeddingModel(ABC):
    name: str
    version: str
    dim: int

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


class HashingEmbeddingModel(EmbeddingModel):
    def __init__(self, dim: int = 256, ngram: int = 3):
        self.name = "hashing-char-ngram"
        self.version = f"v1-d{dim}-n{ngram}"
        self.dim = dim
        self.ngram = ngram

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        for token in re.findall(r"\w+", text.lower()):
            padded = f" {token} "
            for i in range(max(1, len(padded) - self.ngram + 1)):
                digest = hashlib.blake2b(padded[i:i + self.ngram].encode(), digest_size=8).digest()
                bucket = int.from_bytes(digest[:4], "little") % self.dim
                vector[bucket] += 1.0 if digest[4] & 1 else -1.0
        norm = math.sqrt(sum(v * v for v in vector))
        if not norm:
            vector[0] = 1.0
            return vector
        return [v / norm for v in vector]


class SentenceTransformerModel(EmbeddingModel):
    def __init__(self, model_name: str = DEFAULT_ST_MODEL, version: str = "1"):
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)
        self.name = model_name
        self.version = version
        get_dim = getattr(self._model, "get_embedding_dimension", None) or self._model.get_sentence_embedding_dimension
        self.dim = get_dim()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, normalize_embeddings=True, convert_to_numpy=True).tolist()


def load_embedding_model(spec: str | None = None) -> EmbeddingModel:
    spec = spec or os.environ.get("EMBEDDING_MODEL", "hashing")
    if spec == "hashing":
        return HashingEmbeddingModel()
    if spec == "st":
        return SentenceTransformerModel()
    if spec.startswith("st:"):
        return SentenceTransformerModel(spec[3:])
    raise ValueError(f"unknown embedding model '{spec}', use 'hashing', 'st' or 'st:<model name>'")
