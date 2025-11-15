import os
import json
import unicodedata


def load_knowledge(path="data/knowledge/knowledge.json"):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_text(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    ).lower()

def search_knowledge(user_query, knowledge, limit=5):
    query = normalize_text(user_query)
    results = []
    for fragment in knowledge:
        if query in normalize_text(fragment["text"]) or query in normalize_text(fragment["section"]):
            results.append(fragment)
    return results[:limit]

if __name__ == "__main__":
    knowledge_list = load_knowledge()

    print(f"Nombre de fragments chargés : {len(knowledge_list)}")

    query = input("Tape un mot clé à rechercher : ")
    results = search_knowledge(query, knowledge_list)

    print(f"Fragments trouvés pour '{query}':")
    for i, frag in enumerate(results, 1):
        print(f"{i}. [{frag['section']}] {frag['text']}")
