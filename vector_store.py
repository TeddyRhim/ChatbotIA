"""Recherche par sens : embeddings multilingues stockés dans ChromaDB (local, sans serveur)."""
import hashlib
import os
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
DB_PATH = Path(__file__).resolve().parent / "data" / "vectordb"


def fragment_document(fragment):
    """Texte embarqué pour une fiche : son nom, ses alias, puis son contenu."""
    names = ", ".join([fragment.get("subsection", "")] + fragment.get("aliases", []))
    return f"{fragment['section']} - {names}. {fragment['text']}"


class VectorStore:
    def __init__(self, path=DB_PATH, model_name=EMBEDDING_MODEL):
        self.path = Path(path)
        self.model_name = model_name
        self._model = None
        self._client = chromadb.PersistentClient(
            path=str(self.path), settings=Settings(anonymized_telemetry=False)
        )

    @property
    def model(self):
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _embed(self, texts, prefix):
        # Les modèles e5 attendent « passage: » côté documents et « query: » côté questions.
        prefix = prefix if "e5" in self.model_name else ""
        return self.model.encode([prefix + t for t in texts], normalize_embeddings=True).tolist()

    def _signature(self, documents):
        digest = hashlib.sha1("\n".join([self.model_name] + documents).encode("utf-8")).hexdigest()
        return digest

    @property
    def _signature_file(self):
        return self.path / "signature.txt"

    def is_current(self, fragments):
        documents = [fragment_document(f) for f in fragments]
        if not self._signature_file.exists():
            return False
        return self._signature_file.read_text() == self._signature(documents)

    def index(self, fragments):
        """(Ré)indexe toutes les fiches. Rapide : quelques secondes pour quelques centaines de fiches."""
        documents = [fragment_document(f) for f in fragments]
        try:
            self._client.delete_collection("lore")
        except Exception:
            pass
        collection = self._client.create_collection("lore", metadata={"hnsw:space": "cosine"})
        if documents:
            collection.add(
                ids=[str(i) for i in range(len(documents))],
                documents=documents,
                embeddings=self._embed(documents, "passage: "),
            )
        self._signature_file.write_text(self._signature(documents))

    def ensure_index(self, fragments):
        if not self.is_current(fragments):
            self.index(fragments)

    def search(self, question, k=10):
        """Indices (dans la liste de fiches) des fiches les plus proches du sens de la question."""
        collection = self._client.get_collection("lore")
        if collection.count() == 0:
            return []
        result = collection.query(
            query_embeddings=self._embed([question], "query: "),
            n_results=min(k, collection.count()),
        )
        return [int(i) for i in result["ids"][0]]

    def similarities(self, question, indices):
        """Similarité (cosinus) entre la question et des fiches données : {index: score}."""
        if not indices:
            return {}
        collection = self._client.get_collection("lore")
        stored = collection.get(ids=[str(i) for i in indices], include=["embeddings"])
        query = self._embed([question], "query: ")[0]
        return {
            int(i): sum(a * b for a, b in zip(query, vector))
            for i, vector in zip(stored["ids"], stored["embeddings"])
        }
