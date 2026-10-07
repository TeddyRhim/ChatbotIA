"""Évalue les RÉPONSES du chatbot (pas seulement la récupération) sur plusieurs configurations.

    python eval/eval_answers.py                        # toutes les configurations
    python eval/eval_answers.py --configs hybride+liens --limit 5

Jeu de questions : data/lore/_eval_answers.json (privé) sinon data/sample_lore/_eval_answers.json (public).
Critères : voir eval/scoring.py. Les réponses sont générées à température 0,3 : une seule exécution
varie un peu d'un lancement à l'autre, d'où l'option --repeat.
"""
import argparse
import json
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

import ollama  # noqa: E402

from eval.scoring import score_case  # noqa: E402
from main import Chatbot  # noqa: E402
from retrieval import HybridRetriever  # noqa: E402

CONFIGS = ["llm-seul", "mots-clés", "hybride", "hybride+liens"]


def load_cases():
    for candidate in (ROOT / "data" / "lore" / "_eval_answers.json",
                      ROOT / "data" / "sample_lore" / "_eval_answers.json"):
        if candidate.exists():
            return candidate, json.loads(candidate.read_text(encoding="utf-8"))
    sys.exit("Aucun jeu de questions trouvé.")


def make_bot():
    history = Path(tempfile.mkdtemp()) / "history.json"
    return Chatbot(history_file=str(history), context_turns=0)


def run_config(config, bot, question):
    """Retourne (texte, fiches fournies au modèle)."""
    if config == "llm-seul":  # modèle brut : ni notes, ni consignes
        reply = ollama.chat(model=bot.model, messages=[{"role": "user", "content": question}],
                            options={"temperature": 0.3, "num_ctx": 8192})
        return reply["message"]["content"].strip(), []
    result = bot.answer(question, record=False)
    return result["text"], result["fragments"]


def configure(config, bot):
    if config == "mots-clés":
        bot.retriever = HybridRetriever(bot.knowledge_list, store=None, adjacency=bot.retriever.adjacency)
        bot.extra_links = 0
    elif config == "hybride":
        bot.extra_links = 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--configs", default=",".join(CONFIGS))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()

    path, cases = load_cases()
    if args.limit:
        cases = cases[: args.limit]
    configs = args.configs.split(",")
    print(f"{len(cases)} questions ({path.relative_to(ROOT)}), configurations : {', '.join(configs)}, "
          f"{args.repeat} passage(s)\n")

    results = {}
    for config in configs:
        bot = make_bot()
        configure(config, bot)
        rows = []
        for case in cases:
            for _ in range(args.repeat):
                started = time.time()
                text, fragments = run_config(config, bot, case["question"])
                checks, invented = score_case(case, text, fragments)
                rows.append({"question": case["question"], "type": case["type"], "answer": text,
                             "checks": checks, "invented": invented, "seconds": round(time.time() - started, 1)})
            print(f"  [{config}] {case['question'][:60]:<60} {'ok' if rows[-1]['checks']['passed'] else 'ÉCHEC'}",
                  flush=True)
        results[config] = rows

    report(results)
    out = ROOT / "eval" / f"results_{path.parent.name}.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nRéponses détaillées : {out.relative_to(ROOT)} (ignoré par git)")


def rate(rows, key=None):
    if not rows:
        return "  —"
    ok = sum(1 for r in rows if (r["checks"]["passed"] if key is None else r["checks"].get(key, True)))
    return f"{ok / len(rows):.0%}"


def report(results):
    kinds = [("fait", "faits"), ("abstention", "abstention"), ("incertain", "incertitude")]
    print("\n" + f"{'configuration':<16}" + "".join(f"{label:>13}" for _, label in kinds)
          + f"{'ancrage':>10}{'global':>9}{'noms inventés':>15}{'s/réponse':>11}")
    for config, rows in results.items():
        cells = []
        for kind, _ in kinds:
            subset = [r for r in rows if r["type"] == kind]
            cells.append(rate(subset) if subset else "—")
        invented = sum(len(r["invented"]) for r in rows) / len(rows)
        seconds = sum(r["seconds"] for r in rows) / len(rows)
        print(f"{config:<16}" + "".join(f"{c:>13}" for c in cells)
              + f"{rate(rows, 'ancrage'):>10}{rate(rows):>9}{invented:>15.2f}{seconds:>11.1f}")

    last = list(results)[-1]
    failures = [r for r in results[last] if not r["checks"]["passed"]]
    print(f"\nÉchecs de « {last} » ({len(failures)}) :")
    for r in failures:
        failed = [k for k, v in r["checks"].items() if k != "passed" and not v]
        extra = f" noms hors fiches : {', '.join(r['invented'])}" if r["invented"] else ""
        print(f"- {r['question']} → {', '.join(failed)}{extra}")
        print(f"    « {r['answer'][:220].replace(chr(10), ' ')} »")


if __name__ == "__main__":
    main()
