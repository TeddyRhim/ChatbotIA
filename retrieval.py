"""Récupération hybride : mots-clés (noms, alias) + sens (embeddings), fusionnés par rang."""
from knowledge import retrieve as keyword_retrieve

RRF_K = 60  # constante classique de la fusion par rang réciproque


def fuse_rankings(rankings, k):
    """Reciprocal Rank Fusion : une fiche bien classée dans plusieurs listes remonte."""
    scores = {}
    for ranking in rankings:
        for rank, index in enumerate(ranking):
            scores[index] = scores.get(index, 0) + 1 / (RRF_K + rank + 1)
    return sorted(scores, key=lambda index: -scores[index])[:k]


class HybridRetriever:
    def __init__(self, knowledge, store=None, pool=20):
        self.knowledge = knowledge
        self.store = store
        self.pool = pool
        self._index_of = {id(f): i for i, f in enumerate(knowledge)}

    def keyword_indices(self, question, k):
        return [self._index_of[id(f)] for f in keyword_retrieve(question, self.knowledge, k=k)]

    def vector_indices(self, question, k):
        return self.store.search(question, k=k) if self.store else []

    def retrieve(self, question, k=6):
        rankings = [self.keyword_indices(question, self.pool)]
        if self.store:
            rankings.append(self.vector_indices(question, self.pool))
        return [self.knowledge[i] for i in fuse_rankings(rankings, k)]
