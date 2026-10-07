"""Mesure la qualité de la récupération : mots-clés seuls, sens seul, hybride.

Jeu de questions : data/lore/_eval.json (privé) sinon data/sample_lore/_eval.json (public).
Chaque question liste les fiches pertinentes (au moins une doit remonter).
Métriques : hit@k (une fiche pertinente dans les k premières) et MRR (rang de la première).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from knowledge import load_knowledge  # noqa: E402
from retrieval import HybridRetriever, fuse_rankings  # noqa: E402
from vector_store import VectorStore  # noqa: E402


def load_eval():
    for candidate in (ROOT / "data" / "lore" / "_eval.json", ROOT / "data" / "sample_lore" / "_eval.json"):
        if candidate.exists():
            return candidate, json.loads(candidate.read_text(encoding="utf-8"))
    sys.exit("Aucun jeu d'évaluation trouvé.")


def first_rank(names, ranking, expected):
    for rank, name in enumerate(names(ranking), 1):
        if name in expected:
            return rank
    return None


def main():
    path, cases = load_eval()
    knowledge = load_knowledge()
    store = VectorStore()
    store.ensure_index(knowledge)
    retriever = HybridRetriever(knowledge, store)
    name = lambda ranking: [knowledge[i]["subsection"] for i in ranking]

    methods = {
        "mots-clés": lambda q: retriever.keyword_indices(q, 10),
        "sens (embeddings)": lambda q: retriever.vector_indices(q, 10),
        "hybride": lambda q: fuse_rankings([retriever.keyword_indices(q, 20), retriever.vector_indices(q, 20)], 10),
    }

    print(f"{len(cases)} questions ({path.relative_to(ROOT)}), {len(knowledge)} fiches\n")
    print(f"{'méthode':<20}{'hit@3':>8}{'hit@6':>8}{'MRR':>8}")
    ranks_by_method = {}
    for label, run in methods.items():
        ranks = [first_rank(name, run(c["question"]), c["expected"]) for c in cases]
        ranks_by_method[label] = ranks
        hit = lambda k: sum(1 for r in ranks if r and r <= k) / len(ranks)
        mrr = sum(1 / r for r in ranks if r) / len(ranks)
        print(f"{label:<20}{hit(3):>8.0%}{hit(6):>8.0%}{mrr:>8.2f}")

    print("\nQuestions ratées par l'hybride (hors top 6) :")
    for case, rank in zip(cases, ranks_by_method["hybride"]):
        if not rank or rank > 6:
            print(f"- {case['question']}  (attendu : {', '.join(case['expected'])}) → rang {rank}")


if __name__ == "__main__":
    main()
