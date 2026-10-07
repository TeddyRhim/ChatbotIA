"""Mesure la qualité de la récupération : mots-clés seuls, sens seul, hybride, hybride + voisines.

Jeu de questions : data/lore/_eval.json (privé) sinon data/sample_lore/_eval.json (public).
Chaque question liste les fiches pertinentes (`expected` : au moins une doit remonter).
Une question à deux éléments a aussi `also` : une fiche de chaque liste doit remonter.
Métriques : hit@k (une fiche pertinente dans les k premières) et MRR (rang de la première).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from knowledge import load_knowledge  # noqa: E402
from retrieval import HybridRetriever  # noqa: E402
from vector_store import VectorStore  # noqa: E402


def load_eval():
    for candidate in (ROOT / "data" / "lore" / "_eval.json", ROOT / "data" / "sample_lore" / "_eval.json"):
        if candidate.exists():
            return candidate, json.loads(candidate.read_text(encoding="utf-8"))
    sys.exit("Aucun jeu d'évaluation trouvé.")


def main():
    path, all_cases = load_eval()
    simple = [c for c in all_cases if not c.get("also")]
    multi = [c for c in all_cases if c.get("also")]

    knowledge = load_knowledge()
    store = VectorStore()
    store.ensure_index(knowledge)
    retriever = HybridRetriever(knowledge, store)
    names = lambda ranking: [knowledge[i]["subsection"] for i in ranking]

    methods = {
        "mots-clés": lambda q: retriever.keyword_indices(q, 12),
        "sens (embeddings)": lambda q: retriever.vector_indices(q, 12),
        "hybride (12 fiches)": lambda q: retriever.retrieve_indices(q, k=12),
        "hybride 8 + 4 voisines": lambda q: retriever.retrieve_indices(q, k=8, extra=4),
    }

    print(f"{len(simple)} questions simples + {len(multi)} à deux éléments ({path.relative_to(ROOT)}), "
          f"{len(knowledge)} fiches\n")

    print("Questions simples (une fiche à retrouver)")
    print(f"{'méthode':<26}{'hit@3':>8}{'hit@6':>8}{'hit@12':>8}{'MRR':>8}")
    misses = []
    for label, run in methods.items():
        ranks = []
        for case in simple:
            ranking = names(run(case["question"]))
            ranks.append(next((r for r, n in enumerate(ranking, 1) if n in case["expected"]), None))
        hit = lambda k: sum(1 for r in ranks if r and r <= k) / len(ranks)
        mrr = sum(1 / r for r in ranks if r) / len(ranks)
        print(f"{label:<26}{hit(3):>8.0%}{hit(6):>8.0%}{hit(12):>8.0%}{mrr:>8.2f}")
        if label == "hybride 8 + 4 voisines":
            misses = [(c, r) for c, r in zip(simple, ranks) if not r or r > 12]

    if multi:
        print("\nQuestions à deux éléments (les deux fiches doivent remonter)")
        print(f"{'méthode':<26}{'dans 8':>8}{'dans 12':>9}")
        for label, run in methods.items():
            def covered(case, k):
                found = set(names(run(case["question"])[:k]))
                return bool(found & set(case["expected"])) and bool(found & set(case["also"]))
            print(f"{label:<26}{sum(covered(c, 8) for c in multi) / len(multi):>8.0%}"
                  f"{sum(covered(c, 12) for c in multi) / len(multi):>9.0%}")

    for case, rank in misses:
        print(f"\nRatée : {case['question']} (attendu : {', '.join(case['expected'])}) → rang {rank}")


if __name__ == "__main__":
    main()
