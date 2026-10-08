"""Notation déterministe des réponses du chatbot (sans modèle « juge »).

Quatre types de questions :
- fait       : la réponse doit contenir les faits attendus (`facts`), et ces faits doivent se retrouver
               dans les fiches qu'elle cite (« source » : la citation justifie vraiment la réponse).
- abstention : les notes ne disent rien ; la réponse doit le reconnaître au lieu d'inventer.
- incertain  : les notes sont contradictoires ou hypothétiques ; la réponse doit le signaler.
- Dans tous les cas : aucun nom propre de la réponse ne doit être absent des fiches fournies (« ancrage »).

`facts` est une liste de groupes ; chaque groupe est une liste d'alternatives. Tous les groupes doivent
être présents, une alternative suffit par groupe. Comparaison sans accents ni casse.
"""
import re

from knowledge import cited_numbers, normalize_text

SOURCES_MARK = "\n\nSources :\n"

ABSTENTION_MARKERS = [
    "je ne sais pas", "ne sais pas", "ne sait pas", "pas encore ete demand", "pas mentionn", "pas indiqu", "pas precis", "pas explicit",
    "aucune information", "aucun extrait", "ne contien", "ne mentionn", "non mentionn", "pas d'information",
    "pas de mention", "n'est pas dans", "n'apparait pas", "pas dans les extraits", "pas possible de repondre",
    "ne fournissent pas", "ne donnent pas", "ne precis",
    "sans qu'on sache", "sans que l'on sache", "on ne sait pas",
]

UNCERTAINTY_MARKERS = [
    "hypothes", "theorie", "incertain", "a confirmer", "contradict", "contredi", "etre confirm", "ne confirm", "a verifier", "probablement", "pas de consensus", "ambigu",
    "pas confirme", "suppos", "ne le sait pas", "pas clair", "pas certain", "pas etabli", "pas un fait",
    "peut-etre", "pas sur", "selon une note", "controvers", "pas tranch", "discordan", "divergen",
    "reste a clarifier", "a clarifier", "plusieurs versions",
]


def body(text):
    """La réponse sans le bloc « Sources »."""
    return text.split(SOURCES_MARK)[0]


def _contains_any(text, markers):
    normalized = normalize_text(text)
    return any(marker in normalized for marker in markers)


def facts_present(text, groups):
    normalized = normalize_text(body(text))
    return all(any(normalize_text(alt) in normalized for alt in group) for group in groups)


def is_abstention(text):
    return _contains_any(body(text), ABSTENTION_MARKERS)


def flags_uncertainty(text):
    return _contains_any(body(text), UNCERTAINTY_MARKERS)


_NAME = re.compile(r"[A-ZÀ-ÖØ-Ý][\wÀ-ÿ’'-]{3,}")


def proper_names(text):
    """Mots à majuscule hors début de phrase : des noms propres, en pratique."""
    names = []
    for match in _NAME.finditer(text):
        before = text[: match.start()].rstrip()
        if not before or before[-1] in ".!?:\n*#-—>(|]":  # « ] » : fin d'une citation [n], donc début de phrase
            continue
        names.append(match.group(0).strip("'’-"))
    return names


def context_text(question, fragments):
    parts = [question]
    for f in fragments:
        parts += [f["section"], f.get("subsection", ""), " ".join(f.get("aliases", [])), f["text"]]
    return normalize_text(" ".join(parts))


def ungrounded_names(text, question, fragments):
    """Noms propres de la réponse qui n'apparaissent ni dans la question ni dans les fiches fournies."""
    context = context_text(question, fragments)
    return sorted({n for n in proper_names(body(text)) if normalize_text(n) not in context})


def cited_fiches(text, fragments):
    return [fragments[n - 1]["subsection"] for n in cited_numbers(body(text)) if 1 <= n <= len(fragments)]


def cited_text(text, fragments):
    """Contenu (nom, alias, texte) des fiches réellement citées par la réponse."""
    parts = []
    for n in cited_numbers(body(text)):
        if 1 <= n <= len(fragments):
            f = fragments[n - 1]
            parts += [f.get("subsection", ""), " ".join(f.get("aliases", [])), f["text"]]
    return " ".join(parts)


def score_case(case, text, fragments):
    """Renvoie {critère: bool} ; `passed` est vrai si tous les critères applicables sont vrais."""
    kind = case["type"]
    checks = {}
    if kind == "fait":
        checks["faits"] = facts_present(text, case["facts"])
        checks["source"] = facts_present(cited_text(text, fragments), case["facts"])
    elif kind == "abstention":
        checks["abstention"] = is_abstention(text)
    elif kind == "incertain":
        checks["incertitude"] = flags_uncertainty(text)
        if case.get("facts"):
            checks["faits"] = facts_present(text, case["facts"])
    else:
        raise ValueError(f"type de question inconnu : {kind}")
    invented = ungrounded_names(text, case["question"], fragments)
    checks["ancrage"] = not invented
    checks["passed"] = all(checks.values())
    return checks, invented
