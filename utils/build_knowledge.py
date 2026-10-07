import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "data" / "data_raw" / "data_raw.txt"
KNOWLEDGE_PATH = ROOT / "data" / "knowledge" / "knowledge.json"


def is_title(line):
    """Un titre de section est écrit en majuscules (accents compris), hors parenthèses."""
    base = re.sub(r"\(.*?\)", "", line).strip()
    return any(c.isalpha() for c in base) and base == base.upper()


def parse_raw(text):
    """Transforme data_raw.txt en fragments {section, subsection?, text}.

    - une ligne en MAJUSCULES précédée d'une ligne vide ouvre une section ;
    - une autre ligne précédée d'une ligne vide ouvre une sous-section ;
    - chaque ligne commençant par "-" ouvre un fragment, les lignes suivantes le prolongent.
    """
    fragments = []
    section, subsection = "", None
    current = []

    def flush():
        nonlocal current
        if current:
            fragment = {"section": section}
            if subsection:
                fragment["subsection"] = subsection
            fragment["text"] = " ".join(current)
            fragments.append(fragment)
        current = []

    previous_blank = True
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            previous_blank = True
            continue
        if line.startswith("-"):
            flush()
            current = [line[1:].strip()]
        elif previous_blank:
            flush()
            if is_title(line):
                section, subsection = line, None
            else:
                subsection = line
        else:
            current.append(line)
        previous_blank = False
    flush()
    return fragments


def main():
    fragments = parse_raw(RAW_PATH.read_text(encoding="utf-8"))
    KNOWLEDGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(KNOWLEDGE_PATH, "w", encoding="utf-8") as f:
        json.dump(fragments, f, indent=4, ensure_ascii=False)
    print(f"{len(fragments)} fragments écrits dans {KNOWLEDGE_PATH}")


if __name__ == "__main__":
    main()
