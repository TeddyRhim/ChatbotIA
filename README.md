# Chatbot IA - DialoGPT personnalisé

Un chatbot Python basé sur **DialoGPT-medium**, avec historique, mémoire partielle et possibilité de spécialisation via fine-tuning léger (Pas de GPU Cuda donc compliqué de faire mieux).  
Ce projet est conçu pour évoluer, en intégrant à la fois des fonctionnalités interactives et des mécanismes de personnalisation sur mesure.

---

## Fonctionnalités principales

- Chat en temps réel dans le terminal
- Sauvegarde automatique de l’historique (`chat_history.txt`)
- Mode **continue** pour reprendre une conversation
- Recherche dans l’historique (`/search <mot-clé>`)
- Commandes utiles : `/help`, `/quit`, `/continue`, `/clear`
- Fine-tuning léger pour spécialisation sur un univers spécifique
- Préparation automatisée d’une base de connaissance pour l’entraînement futur

---

## Installation

1. Cloner le dépôt :
```bash
git clone git@github.com:ton-utilisateur/ton-depot.git
cd ton-depot

Environnement vituel + activation :

python -m venv venv
source venv/bin/activate  # Linux / macOS
venv\Scripts\activate     # Windows

Installation des dépendances :

pip install -r requirements.txt

Lancement du chat bot (pour le moment) :

python chatbot.py
Commandes disponibles :

/help → liste des commandes
/search <mot> → recherche dans l’historique
/continue → reprendre la dernière conversation
/clear → vider l’historique
/quit → quitter le chat


---

## Roadmap / Évolution du projet

### **Étape 1 : Organisation et nettoyage**
- [x] Structurer les dossiers `data_raw` et `knowledge`
- [x] Créer `main.py` pour le chatbot
- [x] Script `build_knowledge.py` pour générer `knowledge.json`

### **Étape 2 : Knowledge management**
- [x] Créer `knowledge.py` pour gérer les recherches dans le knowledge
- [x] Normalisation du texte pour gérer accents et majuscules
- [ ] Ajouter tags / relations (plus tard, envisager un graphe de connaissances)

### **Étape 3 : Interaction avec le chatbot**
- [x] Recherche dans l’historique utilisateur
- [x] Recherche dans le knowledge automatiquement si non trouvé en mémoire
- [ ] Améliorer la pertinence de la recherche (ex. suggestions, relations entre entités)

### **Étape 4 : Fine-tuning**
- [ ] Préparer `knowledge_dataset.json` pour le fine-tuning
- [ ] Script `build_finetune_dataset.py` pour transformer le knowledge en dataset OpenAI
- [ ] Choisir un modèle de base pour fine-tuning (GPT-3.5 / GPT-4 selon ressources)
- [ ] Entraînement avec LoRA / PEFT
- [ ] Tester le modèle fine-tuné avec `main.py`

### **Étape 5 : Améliorations futures**
- [ ] Intégrer une interface web / GUI
- [ ] Ajouter des suggestions dynamiques du bot basées sur les connexions entre personnages, lieux, objets
- [ ] Gestion automatique des mises à jour du knowledge
- [ ] Optimisation du dataset pour inclure synonymes et variations linguistiques
- [ ] Possibilité de mise à jour via le bot (ajouter du knowledge en live)

---

## Installation

```bash
git clone https://github.com/TeddyRhim/ChatbotIA.git
cd ChatbotIA
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux / Mac
pip install -r requirements.txt


Multi-utilisateur, profils, export du modèle fine-tuné


