"""Liens entre fiches : mentions explicites d'un nom/alias dans le texte, plus le champ `lié:`.

Rien n'est déduit : un lien existe parce que le texte d'une fiche cite le nom (ou un alias
non ambigu) d'une autre fiche, ou parce que tu l'as écrit dans `lié:`.
"""
import math
import re
import sys
from collections import Counter
from pathlib import Path

from knowledge import load_knowledge, normalize_text

MIN_NAME_LEN = 4
# Fiches de synthèse : elles citent tout le monde, mais personne ne les « mentionne ».
# Hors du graphe : elles resteraient voisines de tout et noieraient les vrais liens.
NOT_TARGETS = {"JOURNAL", "THÉORIES"}


def _normalized_names(fragment):
    names = [fragment["subsection"]] + fragment.get("aliases", [])
    return [normalize_text(n).strip() for n in names if len(n.strip()) >= MIN_NAME_LEN]


def build_name_index(knowledge):
    """nom normalisé -> index de la fiche. Un nom principal l'emporte sur un alias ; un alias ambigu est ignoré."""
    primary, aliases = {}, {}
    for i, fragment in enumerate(knowledge):
        if fragment["section"] in NOT_TARGETS:
            continue
        names = _normalized_names(fragment)
        main = normalize_text(fragment["subsection"]).strip()
        for name in names:
            target = primary if name == main else aliases
            target.setdefault(name, set()).add(i)
    index = {name: next(iter(ids)) for name, ids in primary.items() if len(ids) == 1}
    for name, ids in aliases.items():
        if name not in index and len(ids) == 1:
            index[name] = next(iter(ids))
    return index


def _mentions(text, name_index, self_index):
    text = normalize_text(text)
    found = set()
    for name, target in name_index.items():
        if target != self_index and re.search(rf"(?<!\w){re.escape(name)}(?!\w)", text):
            found.add(target)
    return found


def build_adjacency(knowledge, name_index=None):
    """Graphe non orienté : index -> ensemble d'index de fiches liées."""
    name_index = name_index or build_name_index(knowledge)
    adjacency = {i: set() for i in range(len(knowledge))}
    for i, fragment in enumerate(knowledge):
        if fragment["section"] in NOT_TARGETS:
            continue
        body = fragment["text"].split("Faits :", 1)[-1]  # sans la ligne « Alias : ... »
        targets = _mentions(body, name_index, i)
        for ref in fragment.get("liens", []):  # champ `lié:` (noms ou alias)
            ref_index = name_index.get(normalize_text(ref).strip())
            if ref_index is not None and ref_index != i:
                targets.add(ref_index)
        for j in targets:
            adjacency[i].add(j)
            adjacency[j].add(i)
    return adjacency


def neighbors(hits, adjacency, extra, preferred=(), exclude=(), relevance=None):
    """Fiches voisines des fiches trouvées, les plus utiles à la question d'abord.

    `relevance(candidats) -> {index: score}` mesure le rapport de chaque voisine avec la question
    (similarité de sens) ; à défaut, on privilégie celles qui figurent aussi parmi les résultats
    de la recherche (`preferred`). Le nombre de fiches trouvées qui y mènent ne sert qu'à départager.
    """
    counts = Counter()
    for i in hits:
        counts.update(j for j in adjacency.get(i, ()) if j not in hits and j not in exclude)
    scores = relevance(list(counts)) if relevance else {}
    if scores:  # les similarités sont très resserrées : on les étale entre 0 et 1 avant de les combiner
        low, high = min(scores.values()), max(scores.values())
        scores = {j: (v - low) / ((high - low) or 1) for j, v in scores.items()}
    preferred_rank = {index: rank for rank, index in enumerate(preferred)}

    def score(j):
        if scores:
            return scores.get(j, 0) + 0.1 * min(counts[j], 3) / 3
        return counts[j] + (1.5 if j in preferred_rank else 0) - 0.001 * preferred_rank.get(j, 0)

    return sorted(counts, key=score, reverse=True)[:extra]


def bridges(indices, adjacency, top=5):
    """Paires de fiches NON liées entre elles qui partagent des fiches voisines.

    Une voisine commune très connectée (ex. Strahd) compte moins qu'une voisine rare.
    Retourne [(score, a, b, [voisines communes])], les plus fortes d'abord.
    """
    weight = lambda j: 1 / math.log2(2 + len(adjacency[j]))
    found = []
    candidates = [i for i in dict.fromkeys(indices) if adjacency.get(i)]
    for pos, a in enumerate(candidates):
        for b in candidates[pos + 1:]:
            if b in adjacency[a]:
                continue
            shared = sorted(adjacency[a] & adjacency[b], key=weight, reverse=True)
            if shared:
                found.append((sum(weight(j) for j in shared), a, b, shared[:4]))
    return sorted(found, reverse=True)[:top]


def write_report(knowledge, adjacency, path):
    """Rapport lisible pour relire les liens détectés."""
    lines = ["# Liens détectés entre fiches (fichier de travail, ignoré par la construction)", ""]
    for i, fragment in enumerate(knowledge):
        linked = sorted(knowledge[j]["subsection"] for j in adjacency[i])
        lines.append(f"- **{fragment['subsection']}** ({fragment['section']}) → {', '.join(linked) or '—'}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    knowledge = load_knowledge()
    adjacency = build_adjacency(knowledge)
    degrees = sorted((len(v), knowledge[i]["subsection"]) for i, v in adjacency.items())
    print(f"{len(knowledge)} fiches, {sum(len(v) for v in adjacency.values()) // 2} liens")
    print("Fiches sans lien :", [n for d, n in degrees if d == 0])
    print("Les plus liées :", [(n, d) for d, n in degrees[-8:]])
    if len(sys.argv) > 1:
        write_report(knowledge, adjacency, Path(sys.argv[1]))
        print("Rapport écrit :", sys.argv[1])
