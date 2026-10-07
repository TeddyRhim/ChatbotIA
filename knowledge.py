import json
import re
import unicodedata
from pathlib import Path

KNOWLEDGE_PATH = Path(__file__).resolve().parent / "data" / "knowledge" / "knowledge.json"


def load_knowledge(path=KNOWLEDGE_PATH):
    path = Path(path)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    ).lower()


def search_knowledge(user_query, knowledge, limit=5):
    """Retourne les fragments contenant TOUS les mots de la requête (accents et casse ignorés)."""
    words = normalize_text(user_query).split()
    if not words:
        return []
    results = []
    for fragment in knowledge:
        haystack = normalize_text(" ".join([
            fragment["section"], fragment.get("subsection", ""), fragment["text"]
        ]))
        if all(word in haystack for word in words):
            results.append(fragment)
    return results[:limit]


STOPWORDS = {
    "les", "des", "une", "est", "que", "qui", "quoi", "quel", "quels", "quelle", "quelles",
    "dans", "pour", "par", "sur", "avec", "sans", "sont", "ont", "aux", "du", "de", "la", "le",
    "un", "et", "ou", "en", "au", "ce", "ces", "cet", "cette", "il", "elle", "ils", "elles",
    "on", "se", "sa", "son", "ses", "mon", "ma", "mes", "ton", "ta", "tes", "pas", "plus",
    "comment", "pourquoi", "qu", "sais", "sait", "parle", "dis", "moi", "tu", "je", "nous",
}


def _stems(text):
    """Mots normalisés réduits à leurs 5 premières lettres (tolère pluriels et conjugaisons)."""
    return {w[:5] for w in re.findall(r"\w+", normalize_text(text)) if len(w) > 2 and w not in STOPWORDS}


NAME_BONUS = 3


def retrieve(question, knowledge, k=5):
    """Fiches les plus proches d'une question en langage naturel.

    Score = mots communs avec la fiche + NAME_BONUS par mot commun avec son nom ou ses alias.
    Version provisoire par mots-clés : elle sera remplacée par une recherche par embeddings.
    """
    query = _stems(question)
    scored = []
    for fragment in knowledge:
        text = " ".join([fragment["section"], fragment.get("subsection", ""), fragment["text"]])
        names = " ".join([fragment.get("subsection", "")] + fragment.get("aliases", []))
        score = len(query & _stems(text)) + NAME_BONUS * len(query & _stems(names))
        if score:
            scored.append((score, fragment))
    scored.sort(key=lambda pair: -pair[0])
    return [fragment for _, fragment in scored[:k]]


def cited_numbers(text):
    """Numéros cités dans une réponse ([2], [1, 7], [1][4]), dans l'ordre d'apparition, sans doublon."""
    seen = []
    for group in re.findall(r"\[(\d+(?:\s*[,;]\s*\d+)*)\]", text):
        for n in re.findall(r"\d+", group):
            if int(n) not in seen:
                seen.append(int(n))
    return seen


CITATION = re.compile(r"\[\d+(?:\s*[,;]\s*\d+)*\]")
CITATIONS_ONLY = re.compile(r"(?:\[\d+(?:\s*[,;]\s*\d+)*\]\s*)+")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
CITE_MIN_STEMS = 3      # une phrase plus courte n'est pas assez précise pour être rattachée
CITE_MIN_OVERLAP = 0.5  # part des mots de la phrase que la fiche doit contenir


def _fragment_stems(fragments):
    return [_stems(f"{f.get('subsection', '')} {' '.join(f.get('aliases', []))} {f['text']}") for f in fragments]


def _best_fragment(stems, fragment_stems):
    """(index, part des mots de `stems` que la fiche contient) pour la fiche la plus proche."""
    overlaps = [len(stems & s) / len(stems) for s in fragment_stems]
    best = max(range(len(overlaps)), key=overlaps.__getitem__)
    return best, overlaps


def fix_citations(response, fragments):
    """Corrige les citations [n] qui pointent vers une fiche ne contenant pas ce que dit la phrase.

    Chaque citation clôt un morceau de phrase (« Kasimir est elfe [4], frère de Katrina [1] ») : on
    compare ce morceau aux fiches citées. Si aucune ne le contient à moitié et qu'une autre fiche le
    contient clairement, on remplace par celle-ci. Une citation correcte, ou sans meilleure fiche, n'est
    jamais modifiée.
    """
    if not fragments:
        return response
    fragment_stems = _fragment_stems(fragments)
    lines = []
    for line in response.split("\n"):
        out, last = [], 0
        for match in CITATION.finditer(line):
            clause = line[last:match.start()]
            out.append(clause)
            token = match.group(0)
            pieces = [p for p in SENTENCE_END.split(clause.strip()) if p.strip()]
            stems = _stems(pieces[-1]) if pieces else set()
            if len(stems) >= CITE_MIN_STEMS:
                best, overlaps = _best_fragment(stems, fragment_stems)
                cited = [int(n) - 1 for n in re.findall(r"\d+", token) if 1 <= int(n) <= len(fragments)]
                cited_support = max((overlaps[i] for i in cited), default=0)
                if cited_support < CITE_MIN_OVERLAP <= overlaps[best] and best not in cited:
                    token = f"[{best + 1}]"
            out.append(token)
            last = match.end()
        out.append(line[last:])
        lines.append("".join(out))
    return "\n".join(lines)


def ensure_citations(response, fragments):
    """Fiabilise les citations d'une réponse : corrige celles qui visent la mauvaise fiche, puis ajoute
    [n] aux phrases restées sans citation quand une fiche les contient clairement.

    Filet de sécurité déterministe (recouvrement de mots) : une phrase trop courte, ou sans fiche
    convaincante, reste telle quelle.
    """
    if not fragments:
        return response
    response = fix_citations(response, fragments)
    fragment_stems = _fragment_stems(fragments)
    lines = []
    for line in response.split("\n"):
        segments = []
        for part in SENTENCE_END.split(line):
            leading = CITATIONS_ONLY.match(part)  # « Phrase. [1] Suite » : le [1] appartient à « Phrase. »
            if segments and leading:
                segments[-1] += " " + leading.group(0).strip()
                part = part[leading.end():]
                if not part.strip():
                    continue
            segments.append(part)
        sentences = []
        for sentence in segments:
            stems = _stems(sentence)
            if CITATION.search(sentence) or len(stems) < CITE_MIN_STEMS:
                sentences.append(sentence)
                continue
            best, overlaps = _best_fragment(stems, fragment_stems)
            sentences.append(f"{sentence} [{best + 1}]" if overlaps[best] >= CITE_MIN_OVERLAP else sentence)
        lines.append(" ".join(sentences))
    return "\n".join(lines)


def format_label(fragment):
    """Étiquette courte d'une fiche, pour afficher les sources."""
    label = fragment["section"]
    if fragment.get("subsection"):
        label += f" > {fragment['subsection']}"
    return f"[{label}]"


def format_fragment(fragment):
    return f"{format_label(fragment)} {fragment['text']}"


if __name__ == "__main__":
    knowledge_list = load_knowledge()

    print(f"Nombre de fragments chargés : {len(knowledge_list)}")

    query = input("Tape un mot clé à rechercher : ")
    results = search_knowledge(query, knowledge_list)

    print(f"Fragments trouvés pour '{query}':")
    for i, frag in enumerate(results, 1):
        print(f"{i}. {format_fragment(frag)}")
