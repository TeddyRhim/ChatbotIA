"""Récupération hybride : mots-clés (noms, alias) + sens (embeddings), fusionnés par rang."""
from graph import build_adjacency, neighbors
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
    def __init__(self, knowledge, store=None, pool=20, adjacency=None, seeds=8):
        self.knowledge = knowledge
        self.store = store
        self.pool = pool
        self.seeds = seeds  # nombre de meilleures fiches dont on explore les voisines
        self.adjacency = adjacency if adjacency is not None else build_adjacency(knowledge)
        self._index_of = {id(f): i for i, f in enumerate(knowledge)}

    def keyword_indices(self, question, k):
        return [self._index_of[id(f)] for f in keyword_retrieve(question, self.knowledge, k=k)]

    def vector_indices(self, question, k):
        return self.store.search(question, k=k) if self.store else []

    def ranking(self, question, k):
        rankings = [self.keyword_indices(question, self.pool)]
        if self.store:
            rankings.append(self.vector_indices(question, self.pool))
        return fuse_rankings(rankings, k)

    def retrieve_indices(self, question, k=8, extra=0):
        """k fiches les plus pertinentes, suivies de `extra` fiches voisines (liées aux meilleures)."""
        pool = self.ranking(question, self.pool)
        top = pool[:k]
        if extra:
            seeds = [i for i in top if self.adjacency.get(i)][: self.seeds]  # fiches qui ont des liens
            relevance = (lambda candidates: self.store.similarities(question, candidates)) if self.store else None
            top = top + neighbors(seeds, self.adjacency, extra, preferred=pool[k:],
                                  exclude=set(top), relevance=relevance)
        return top

    def retrieve(self, question, k=8, extra=0):
        return [self.knowledge[i] for i in self.retrieve_indices(question, k, extra)]
