import json
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


def format_fragment(fragment):
    label = fragment["section"]
    if fragment.get("subsection"):
        label += f" > {fragment['subsection']}"
    return f"[{label}] {fragment['text']}"


if __name__ == "__main__":
    knowledge_list = load_knowledge()

    print(f"Nombre de fragments chargés : {len(knowledge_list)}")

    query = input("Tape un mot clé à rechercher : ")
    results = search_knowledge(query, knowledge_list)

    print(f"Fragments trouvés pour '{query}':")
    for i, frag in enumerate(results, 1):
        print(f"{i}. {format_fragment(frag)}")
