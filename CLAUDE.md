# ChatbotIA

Chatbot RAG local en français : il répond à partir d'une base de fiches (un univers de jeu de rôle), cite ses sources [1], [2] et dit « je ne sais pas » quand rien de pertinent n'est trouvé. LLM Qwen2.5 7B via Ollama, embeddings multilingual-e5-small dans ChromaDB, recherche hybride (mots-clés, sens, graphe de liens entre fiches). Tout reste en local.

## Commandes
- Installer : `python -m venv venv`, `venv\Scripts\activate`, `pip install -r requirements.txt`, puis `ollama pull qwen2.5:7b`. Les dépendances du dossier `legacy/` (PyTorch) sont dans `requirements-legacy.txt`.
- Construire la base : `python utils/build_knowledge.py` (à relancer après toute modification des fiches).
- Interface : `streamlit run interface.py`. Terminal : `python console_chat.py`.
- Tests : `python -m unittest discover -s tests -t .` (les tests utilisent `data/sample_lore`, jamais les vraies fiches).
- Évaluation de la récupération : `python eval/eval_retrieval.py`. Évaluation des réponses : `python eval/eval_answers.py [--configs a,b] [--limit N] [--repeat N]` (appelle Ollama, plusieurs minutes, écrit `eval/results_*.json`).
- Pas de linter configuré.

## Prérequis
- Python 3.11, Ollama lancé en service local avec `qwen2.5:7b`. Le premier lancement télécharge le modèle d'embeddings.
- Variables : `LORE_DIR` (dossier des fiches ; sinon `data/lore/` s'il contient des fiches, sinon `data/sample_lore/`), `EMBEDDING_MODEL`. Ce ne sont pas des secrets et aucun `.env` n'est chargé.
- `main.py` libère le modèle 2 minutes après la dernière question (`keep_alive`).

## Structure
- `main.py` (classe Chatbot), `knowledge.py` (chargement, recherche, citations), `retrieval.py` et `vector_store.py` (ChromaDB, fusion hybride), `graph.py` (liens entre fiches), `interface.py` (Streamlit), `console_chat.py`.
- `eval/` : évaluations et notation déterministe (`scoring.py`, sans modèle juge). Écarts de 0 à 3 points entre configurations : du bruit, pas un signal.
- `legacy/` : fine-tuning LoRA abandonné, ne pas y investir.

## Données privées (jamais dans git)
`data/lore/`, `data/data_raw/`, `chat_history.json`, `data/knowledge/*.json`, `data/vectordb/`, `data/lora_finetuned/`, `eval/results_*.json`, `venv/`, `assets/ambiance.*`. Les vraies fiches ne sont jamais citées dans le code, les tests, les commits ni le README : utiliser `data/sample_lore` pour tout exemple. Captures d'écran et tests avec l'univers d'exemple uniquement.

## Règles pour les fiches de connaissance
- Une fiche tient en quelques milliers de caractères, le fait principal en premier (contexte de 8192 jetons, sinon réponses « je ne sais pas » à tort).
- Une théorie porte une étiquette (hypothèse, à confirmer). Un personnage mort est au passé partout. Une absence d'information s'écrit dans la fiche.
- Les fichiers dont le nom commence par `_` sont ignorés par le build.

## Pièges
- Le README contient des chiffres d'évaluation qui datent de versions différentes : les mettre à jour ensemble, jamais un seul.
- Pour lancer une évaluation longue, la lancer en arrière-plan et prévenir à la fin ; Ollama doit tourner.
