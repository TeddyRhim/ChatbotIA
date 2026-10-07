"""Construit data/knowledge/knowledge.json à partir de fiches Markdown.

Les fiches privées sont dans data/lore/ (ignoré par git). Sans elles, ou avec
LORE_DIR non défini, on retombe sur le jeu d'exemple public data/sample_lore/.

Format d'une fiche (un fichier par catégorie : personnages.md, lieux.md, ...) :

    # Nom
    alias: Autre nom, Autre orthographe
    statut: en cours
    - fait établi
    - (hypothèse) idée du joueur, pas un fait
    - (à confirmer) point contradictoire ou incertain
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIVATE_LORE = ROOT / "data" / "lore"
SAMPLE_LORE = ROOT / "data" / "sample_lore"
KNOWLEDGE_PATH = ROOT / "data" / "knowledge" / "knowledge.json"

SECTION_LABELS = {
    "personnages": "PERSONNAGES",
    "lieux": "LIEUX",
    "objets": "OBJETS",
    "factions": "FACTIONS",
    "quetes": "QUÊTES",
    "concepts": "CONCEPTS",
    "journal": "JOURNAL",
    "theories": "THÉORIES",
}


def lore_dir():
    """Dossier des fiches : LORE_DIR, sinon data/lore/ s'il contient des fiches, sinon l'exemple public."""
    if os.environ.get("LORE_DIR"):
        return Path(os.environ["LORE_DIR"])
    if any(_lore_files(PRIVATE_LORE)):
        return PRIVATE_LORE
    return SAMPLE_LORE


def _lore_files(directory):
    """Fichiers .md de fiches (ceux qui commencent par _ sont des notes de travail ignorées)."""
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.glob("*.md") if not p.name.startswith("_"))


def _render(meta, facts):
    parts = []
    if meta.get("alias"):
        parts.append(f"Alias : {meta['alias']}.")
    if meta.get("statut"):
        parts.append(f"Statut : {meta['statut']}.")
    if facts:
        parts.append("Faits : " + " ; ".join(facts))
    return " ".join(parts)


def parse_fiches(text, section):
    """Transforme le texte d'un fichier en fragments {section, subsection (nom), aliases, text}."""
    fragments = []
    current = None

    def flush():
        if current and (current["facts"] or current["meta"]):
            fragments.append({
                "section": section,
                "subsection": current["name"],
                "aliases": [a.strip() for a in current["meta"].get("alias", "").split(",") if a.strip()],
                "text": _render(current["meta"], current["facts"]),
            })

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("# "):
            flush()
            current = {"name": line[2:].strip(), "meta": {}, "facts": []}
        elif not line or current is None:
            continue
        elif line.startswith("- "):
            current["facts"].append(line[2:].strip())
        elif current["facts"]:
            current["facts"][-1] += " " + line  # ligne de continuation
        elif ":" in line:
            key, value = line.split(":", 1)
            current["meta"][key.strip().lower()] = value.strip()
    flush()
    return fragments


def build(directory=None):
    directory = Path(directory) if directory else lore_dir()
    fragments = []
    for path in _lore_files(directory):
        section = SECTION_LABELS.get(path.stem, path.stem.upper())
        fragments += parse_fiches(path.read_text(encoding="utf-8"), section)
    return fragments


def main():
    directory = lore_dir()
    fragments = build(directory)
    KNOWLEDGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(KNOWLEDGE_PATH, "w", encoding="utf-8") as f:
        json.dump(fragments, f, indent=2, ensure_ascii=False)
    print(f"{len(fragments)} fiches issues de {directory} écrites dans {KNOWLEDGE_PATH}")


if __name__ == "__main__":
    main()
