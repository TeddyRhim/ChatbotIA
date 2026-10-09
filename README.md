# Chatbot IA : RAG local en français (Ollama)

Un chatbot qui répond à partir d'une base de fiches (ici, un univers de jeu de rôle inventé), cite ses sources `[1]`, `[2]` et dit « je ne sais pas » quand rien de pertinent n'est trouvé. Tout reste en local : LLM Qwen2.5 7B via [Ollama](https://ollama.com), embeddings `multilingual-e5-small` dans ChromaDB, aucun service en ligne.

Développé et testé sur Windows 11 (GTX 1070 8 Go, 16 Go de RAM), Python 3.11.

## Aperçu

Interface web Streamlit sur l'univers d'exemple `data/sample_lore/` : une réponse prudente avec sa source, puis un « je ne sais pas » quand l'information n'existe pas. Les captures montrent le thème précédent ; l'interface actuelle est plus sombre (voir Fonctionnalités).

| Question sur une hypothèse | Source citée, puis abstention |
| --- | --- |
| ![Question sur une hypothèse](docs/screenshots/chat-1.jpg) | ![Source citée dépliée, puis je ne sais pas](docs/screenshots/chat-2.jpg) |

## Fonctionnalités

- **Recherche hybride** : mots-clés (noms, alias) et sens (embeddings), fusionnés par RRF, complétés par les fiches voisines d'un graphe de liens (mentions d'un nom ou alias, champ `lié:`).
- **Réponses sourcées** : citations `[n]` vérifiées après coup (une citation qui ne correspond pas à la fiche est corrigée), bloc « Sources » replié sous chaque réponse.
- **Hypothèses étiquetées** : ce qui est marqué `(hypothèse)`, `(théorie)` ou `(à confirmer)` n'est pas présenté comme un fait.
- **Mode `piste <sujet>`** : liste d'abord les points encore ouverts des notes (extraits sans modèle de langage), puis 0 à 3 hypothèses du LLM, chacune appuyée sur deux extraits ; sinon « Aucune piste solide ».
- **`search <mots>`** : recherche dans les fiches (tous les mots doivent apparaître, accents et casse ignorés), puis dans l'historique.
- **Interfaces** : terminal (`console_chat.py`) et web (`interface.py`). Thème gothique sombre en CSS local (brume, pluie, vignette, éclair unique à l'ouverture, animations coupées si le système le demande) et lecteur de musique d'ambiance facultatif (`assets/ambiance.mp3`, jamais versionné).
- **Historique** sauvegardé dans `chat_history.json` (ignoré par git), les 3 derniers échanges sont transmis au modèle. Le modèle est déchargé de la mémoire 2 minutes après la dernière question.

## Installation

```bash
git clone https://github.com/TeddyRhim/ChatbotIA.git
cd ChatbotIA
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
pip install -r requirements.txt
ollama pull qwen2.5:7b
python utils/build_knowledge.py
```

`build_knowledge.py` construit `data/knowledge/knowledge.json` à partir de `data/lore/` s'il contient des fiches, sinon de l'exemple `data/sample_lore/` ; à relancer après toute modification des fiches. La variable `LORE_DIR` force un autre dossier. Le premier lancement télécharge le modèle d'embeddings.

## Utilisation

Ollama doit tourner.

```bash
python console_chat.py        # terminal : search <mots>, piste <sujet>, reset, quit
streamlit run interface.py    # interface web
```

## Les fiches

Une fiche par personnage, lieu, objet ou quête : un nom, des alias, un statut, des faits. Les champs `alias:`, `statut:` et `lié:` précèdent les puces. Le fait principal vient en premier et la fiche reste courte (contexte du modèle : 8 192 jetons).

```markdown
# Elowen Brindelune
alias: Elowen, la Gardienne
statut: alliée
- Gardienne de la tour de Vélan.
- (hypothèse) Elle serait la sœur disparue du roi Maren.
```

- `data/sample_lore/` : univers d'exemple (9 fiches), versionné, utilisé par défaut et par les tests.
- `data/lore/` et `data/data_raw/` : données privées, ignorées par git.
- Les fichiers dont le nom commence par `_` sont des notes de travail, ignorés par la construction.

## Tests

```bash
python -m unittest discover -s tests -t .
```

Les tests utilisent uniquement `data/sample_lore`. Une CI GitHub Actions les lance à chaque push et pull request.

## Évaluation

- `python eval/eval_retrieval.py` : récupération (hit@k, MRR) pour mots-clés, sens et hybride.
- `python eval/eval_answers.py [--configs a,b] [--limit N] [--repeat N]` : réponses, avec une notation déterministe sans modèle juge (faits attendus, faits présents dans les fiches citées, abstention, réserve, aucun nom propre absent des fiches). Appelle Ollama, plusieurs minutes.
- Jeu d'exemple public : 5 questions de récupération (`data/sample_lore/_eval.json`) et 8 questions de réponses (4 faits, 2 abstentions, 2 incertains, `_eval_answers.json`). Il sert à démontrer la méthode, pas à produire des chiffres.

Dernière mesure documentée : 2026-10-09, sur les 192 fiches privées de l'auteur, 113 questions, 2 passages : 95 % de réussite globale en hybride, 98 % en hybride + liens. L'écart entre les deux est dans le bruit de mesure (0 à 3 points). Ces fichiers de résultats ne sont pas versionnés ; la méthode, l'historique daté de chaque mesure et les enseignements sont dans [docs/evaluation.md](docs/evaluation.md).

## Limites connues

- Un modèle de 7 milliards de paramètres comble volontiers les vides : une absence d'information doit être écrite dans la fiche.
- Les réponses très courtes ne sont pas toujours rattachées à une fiche ; une réponse peut être juste mais incomplète.
- Une théorie de joueur n'est pas toujours présentée comme telle si la fiche ne l'étiquette pas.
- Les mesures reposent sur un petit jeu de test écrit par l'auteur, avec 1 à 2 points de bruit entre deux passages.

## Organisation

- `main.py` : classe `Chatbot` (Ollama, historique, génération). `knowledge.py` : chargement, recherche, citations.
- `vector_store.py`, `retrieval.py` : embeddings (ChromaDB, index dans `data/vectordb/`, reconstruit automatiquement) et fusion hybride. `graph.py` : liens entre fiches.
- `interface.py`, `console_chat.py` : interfaces. `utils/build_knowledge.py` : construction de la base.
- `eval/` : évaluations et notation. `tests/` : tests unitaires. `docs/` : captures et évaluation détaillée.
- `legacy/` : expérience de fine-tuning LoRA de GPT-2 (abandonnée : peu de données, modèle peu adapté au français). Ses dépendances sont dans `requirements-legacy.txt`.

## Licence

MIT, voir [LICENSE](LICENSE).
