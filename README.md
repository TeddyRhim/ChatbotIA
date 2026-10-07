# Chatbot IA - RAG local (Ollama)

Un chatbot Python en français qui répond à partir d'une **base de connaissances** (un univers de jeu de rôle inventé), avec sources citées. Il utilise un LLM local (**Qwen2.5 7B via Ollama**) : les extraits pertinents sont injectés dans le prompt (RAG). Une expérience de fine-tuning LoRA (GPT-2) est conservée dans `legacy/`.

> Le projet évolue vers un chatbot RAG 100 % local : voir [Futur du projet](#futur-du-projet--pivot-vers-un-chatbot-rag-100--local).

* Le fine-tuning n’a pas pu être conclu (dataset trop limité, modèle inadapté au français).
* Les scripts de `legacy/` redirigent le cache HuggingFace vers `D:\huggingface_cache` (manque de place sur C:). Supprimez la ligne `os.environ["HF_HOME"]` de `legacy/finetune_lora.py` si vous n'en avez pas besoin.

---

## Fonctionnalités principales

- Chat en temps réel dans le terminal (`console_chat.py`) ou dans une interface web Streamlit (`interface.py`)
- Historique sauvegardé automatiquement (`chat_history.json`, ignoré par git) et repris au lancement
- Contexte des derniers échanges transmis au modèle
- Réponses fondées sur les extraits retrouvés, avec sources affichées (« Je ne sais pas » si rien de pertinent)
- `search <mots>` : recherche dans la base de connaissances (tous les mots doivent apparaître, accents et casse ignorés), puis dans l’historique
- Commandes du terminal : `search`, `reset`, `quit`
- Tests unitaires de la recherche et de la construction de la base (`tests/`)

---

## Organisation des fichiers

- `main.py` : classe `Chatbot` (Ollama, historique, récupération des extraits, génération).
- `console_chat.py` / `interface.py` : interfaces terminal et web.
- `knowledge.py` : chargement, recherche `search` et récupération par mots-clés (noms, alias).
- `vector_store.py` / `retrieval.py` : recherche par sens (embeddings `multilingual-e5-small` dans ChromaDB, index dans `data/vectordb/`, reconstruit automatiquement) et fusion hybride avec les mots-clés.
- `eval/eval_retrieval.py` : compare mots-clés, sens et hybride (hit@k, MRR) sur un jeu de questions (`_eval.json`).
- `data/lore/` : fiches de l'univers (privé) ; `data/sample_lore/` : exemple public ; `data/data_raw/` : notes brutes (privé).
- `data/knowledge/knowledge.json` : base générée par `utils/build_knowledge.py` (non versionnée).
- `tests/` : tests unitaires (`python -m unittest discover -s tests -t .`).
- `legacy/` : tentative de fine-tuning LoRA (`finetune_lora.py`, `test_lora.py`).

---

## Knowledge Base : des fiches, pas des puces

Les notes brutes sont transformées en **fiches** (une par personnage, lieu, objet, quête...), chacune avec un nom, des alias (orthographes variantes) et des faits. Les suppositions du joueur sont marquées `(hypothèse)`, `(théorie)` ou `(à confirmer)` pour que le chatbot ne les présente pas comme des faits.

```markdown
# Elowen Brindelune
alias: Elowen, la Gardienne
statut: alliée
- Gardienne de la tour de Vélan.
- (hypothèse) Elle serait la sœur disparue du roi Maren.
```

- `data/sample_lore/` : univers fictif d'exemple, versionné, utilisé par défaut (et par les tests).
- `data/lore/` et `data/data_raw/` : **données privées** (notes de campagne et fiches), ignorées par git. Ordre de choix : variable `LORE_DIR` si définie, sinon `data/lore/` s'il contient des fiches, sinon l'exemple.
- `utils/build_knowledge.py` transforme les fiches en `data/knowledge/knowledge.json`.
- Les fichiers `_*.md` (ex. `_a_clarifier.md`) sont des notes de travail, ignorées par la construction.

---

## Roadmap / Évolution du projet

### **Étape 1 : Organisation et nettoyage**
- [x] Structurer les dossiers `data_raw` et `knowledge`
- [x] Créer `main.py` pour le chatbot
- [x] Script `build_knowledge.py` pour générer `knowledge.json`

### **Étape 2 : Knowledge management**
- [x] Créer `knowledge.py` pour gérer les recherches dans le knowledge
- [x] Normalisation du texte pour gérer accents et majuscules

### **Étape 3 : Interaction avec le chatbot**
- [x] Recherche dans l’historique utilisateur
- [x] Recherche dans le knowledge automatiquement si non trouvé en mémoire

### **Étape 4 : Fine-tuning**
- [x] Préparer `knowledge_dataset.json` pour le fine-tuning
- [x] Script de construction du dataset de fine-tuning (supprimé ensuite, voir `legacy/`)
- [x] Choisir un modèle de base pour fine-tuning (GTP2)
- [x] Entraînement avec LoRA / PEFT
- [-] Tester le modèle fine-tuné avec `main.py`

### **Étape 5 : Améliorations futures**
- [ ] Intégrer une interface web / GUI
- [-] Ajouter des suggestions dynamiques du bot basées sur les connexions entre personnages, lieux, objets
- [ ] Gestion automatique des mises à jour du knowledge
- [?] Possibilité de mise à jour via le bot (ajouter du knowledge en live)

---

## Futur du projet : pivot vers un chatbot RAG 100 % local

**Bilan de la première version.** DialoGPT / GPT-2 sont des modèles de 2019-2020, surtout anglophones : leurs réponses restent incohérentes, et le fine-tuning LoRA n'a pas pu aboutir (48 exemples seulement, modèle inadapté au français, PyTorch installé en version CPU alors que la machine dispose d'une GTX 1070). Le fine-tuning n'est de toute façon plus la bonne approche pour « faire connaître » un univers à un modèle.

**Direction actuelle : RAG (Retrieval-Augmented Generation).** Au lieu d'entraîner le modèle, on lui fournit à chaque question les passages pertinents de la base de connaissances. Modifier le contenu met le bot à jour immédiatement, sans réentraînement.

Objectifs, tout en local et gratuit :

1. ✅ **Modèle de génération** : DialoGPT remplacé par un LLM récent (Qwen2.5 7B ou équivalent, en 4 bits) servi par [Ollama](https://ollama.com).
2. ✅ **Base vectorielle** : découper les documents, calculer des embeddings multilingues (`multilingual-e5-small` ou `bge-m3`) et les stocker dans ChromaDB, à la place de la recherche par mot-clé de `knowledge.py`.
3. ✅ **Sources citées** (première version) : réponses fondées uniquement sur les passages retrouvés, avec références `[1]`, `[2]`, et un « je ne sais pas » quand rien de pertinent n'est trouvé.
4. ✅ **Évaluation** (récupération ; évaluation des réponses à venir) : jeu de 30 à 50 questions avec réponses attendues, mesure du retrieval (hit rate, MRR) et de la fidélité des réponses, pour comparer les configurations avec des chiffres.
5. **Interface** : conserver Streamlit (`interface.py`) en affichant les sources sous chaque réponse.

Ce qui est conservé : l'historique de conversation, la base `knowledge.json` (comme premier corpus) et l'interface web. Le code LoRA reste dans `utils/` comme trace de l'expérimentation.

Résultats actuels de la récupération (25 questions de test, 156 fiches) : hit@6 = 88 % mots-clés seuls, 92 % sens seul, **96 % hybride** (`python eval/eval_retrieval.py`).

À venir : liens explicites entre fiches (récupération des fiches voisines) et un mode `piste` qui propose des liens non écrits, étiquetés comme hypothèses et sourcés.

Pistes ultérieures : ajout de documents personnels (PDF, notes), mise à jour de la base depuis le chat, multi-utilisateur et profils.

---

## Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/TeddyRhim/ChatbotIA.git
cd ChatbotIA
```

2. Environnement virtuel + activation :
```bash
python -m venv venv
source venv/bin/activate  # Linux / macOS
venv\Scripts\activate     # Windows
```

3. Installation des dépendances (et d'[Ollama](https://ollama.com), puis `ollama pull qwen2.5:7b`) :
```bash
pip install -r requirements.txt
```

4. Génération de la base de connaissances (à partir de `data/lore/` si présent, sinon de l'exemple `data/sample_lore/`) :
```bash
python utils/build_knowledge.py
```

5. Lancement (Ollama doit tourner) :
```bash
python console_chat.py        # chat dans le terminal
streamlit run interface.py    # interface web
```

Commandes du chat terminal :

- `search <mot>` → recherche dans l'historique puis dans le knowledge
- `reset` → vider l'historique
- `quit` → quitter


