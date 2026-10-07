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
    """Numéros [n] cités dans une réponse, dans l'ordre d'apparition, sans doublon."""
    seen = []
    for n in re.findall(r"\[(\d+)\]", text):
        if int(n) not in seen:
            seen.append(int(n))
    return seen


CITATION = re.compile(r"\[\d+(?:\s*[,;]\s*\d+)*\]")
CITATIONS_ONLY = re.compile(r"(?:\[\d+(?:\s*[,;]\s*\d+)*\]\s*)+")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
CITE_MIN_STEMS = 3      # une phrase plus courte n'est pas assez précise pour être rattachée
CITE_MIN_OVERLAP = 0.5  # part des mots de la phrase que la fiche doit contenir


def ensure_citations(response, fragments):
    """Ajoute [n] aux phrases sans citation quand une fiche les contient clairement.

    Filet de sécurité quand le modèle oublie de citer : chaque phrase est rattachée à la fiche qui
    partage le plus de ses mots (au moins la moitié). Les phrases déjà citées, trop courtes ou
    sans fiche convaincante restent telles quelles.
    """
    if not fragments:
        return response
    fragment_stems = [_stems(f"{f.get('subsection', '')} {' '.join(f.get('aliases', []))} {f['text']}")
                      for f in fragments]
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
            overlaps = [len(stems & s) / len(stems) for s in fragment_stems]
            best = max(range(len(overlaps)), key=overlaps.__getitem__)
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
