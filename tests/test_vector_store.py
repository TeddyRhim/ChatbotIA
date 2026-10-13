import math
import tempfile
import unittest
import zlib

from vector_store import VectorStore

KNOWLEDGE = [
    {"section": "PERSONNAGES", "subsection": "Elowen", "aliases": [], "text": "gardienne tour lanterne"},
    {"section": "LIEUX", "subsection": "Phare", "aliases": [], "text": "phare mer falaise"},
    {"section": "OBJETS", "subsection": "Lame", "aliases": [], "text": "epee lame argent"},
]


class FakeEncoder:
    """Encodeur déterministe : un sac de mots projeté sur 32 dimensions, sans téléchargement."""

    def __init__(self):
        self.calls = 0

    def encode(self, texts, normalize_embeddings=True):
        self.calls += 1
        vectors = []
        for text in texts:
            vector = [0.0] * 32
            for word in text.lower().replace(".", " ").replace(",", " ").split():
                vector[zlib.crc32(word.encode()) % 32] += 1.0
            norm = math.sqrt(sum(v * v for v in vector)) or 1.0
            vectors.append(_Array([v / norm for v in vector]))
        return _Array(vectors)


class _Array(list):
    def tolist(self):
        return [list(v) for v in self] if self and isinstance(self[0], list) else list(self)


class VectorStoreTest(unittest.TestCase):
    def setUp(self):
        # Sous Windows, ChromaDB garde ses fichiers ouverts : le nettoyage peut échouer sans gravité.
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.store = VectorStore(path=self.tmp.name, model_name="intfloat/multilingual-e5-small")
        self.encoder = FakeEncoder()
        self.store._model = self.encoder

    def tearDown(self):
        del self.store
        self.tmp.cleanup()

    def test_index_then_search_finds_the_closest_fiche(self):
        self.store.ensure_index(KNOWLEDGE)
        self.assertEqual(self.store.search("le phare sur la falaise", k=1), [1])

    def test_signature_avoids_reindexing_unchanged_fiches(self):
        self.store.ensure_index(KNOWLEDGE)
        self.assertTrue(self.store.is_current(KNOWLEDGE))
        calls = self.encoder.calls
        self.store.ensure_index(KNOWLEDGE)
        self.assertEqual(self.encoder.calls, calls)

    def test_changed_fiches_are_reindexed(self):
        self.store.ensure_index(KNOWLEDGE)
        changed = KNOWLEDGE[:2] + [{**KNOWLEDGE[2], "text": "bouclier bronze"}]
        self.assertFalse(self.store.is_current(changed))
        self.store.ensure_index(changed)
        self.assertEqual(self.store.search("bouclier bronze", k=1), [2])

    def test_question_is_embedded_once_for_search_and_similarities(self):
        self.store.ensure_index(KNOWLEDGE)
        calls = self.encoder.calls
        self.store.search("lame argent", k=2)
        scores = self.store.similarities("lame argent", [0, 2])
        self.assertEqual(self.encoder.calls, calls + 1)
        self.assertGreater(scores[2], scores[0])


if __name__ == "__main__":
    unittest.main()
