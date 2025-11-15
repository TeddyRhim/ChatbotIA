# Chatbot IA - DialoGPT / ChatbotIA personnalisé

Un chatbot Python basé sur **DialoGPT-medium** (ou GPT-2 pour tests LoRA), avec historique, mémoire partielle et possibilité de spécialisation via fine-tuning léger.  
Ce projet est conçu pour évoluer, en intégrant à la fois des fonctionnalités interactives et des mécanismes de personnalisation sur mesure, tout en exploitant un **knowledge base** statique pour guider les réponses.
* Le fine-tuning n’a pas pu être conclu en raison d’un dataset trop limité. Étant donné que l’utilisation reste personnelle, je ne cherche pas encore à enrichir les données.
---

## Fonctionnalités principales

- Chat en temps réel dans le terminal
- Sauvegarde automatique de l’historique (`chat_history.txt`)
- Mode **continue** pour reprendre une conversation
- Recherche dans l’historique (`/search <mot-clé>`)
- Recherche dans un **knowledge.json** contenant des informations sur l’univers
- Commandes utiles : `/help`, `/quit`, `/continue`, `/clear`
- Tentative de fine-tuning léger via LoRA pour spécialisation sur un univers
- Préparation automatisée d’une base de connaissance pour un apprentissage futur

---

## Organisation des fichiers

- `main.py` : Point d’entrée du chatbot. Utilise le `knowledge.json` pour répondre aux questions via un moteur de recherche simple.
- `data/knowledge/knowledge.json` : Base de connaissances structurée.
- `utils/finetune_lora.py` : Tentative de fine-tuning LoRA pour entraîner le modèle sur le knowledge.
- `utils/test_lora.py` : Script de test pour le modèle LoRA fine-tuné.
- `chat_history.txt` : Sauvegarde des conversations.

---

## Knowledge Base

- **Format JSON** : `"prompt"` / `"response"`  
- Exemple d’entrée :

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
- [x] Script `build_knowledge.py` pour transformer le knowledge en dataset OpenAI
- [x] Choisir un modèle de base pour fine-tuning (GTP2)
- [x] Entraînement avec LoRA / PEFT
- [-] Tester le modèle fine-tuné avec `main.py`

### **Étape 5 : Améliorations futures**
- [ ] Intégrer une interface web / GUI
- [-] Ajouter des suggestions dynamiques du bot basées sur les connexions entre personnages, lieux, objets
- [ ] Gestion automatique des mises à jour du knowledge
- [?] Possibilité de mise à jour via le bot (ajouter du knowledge en live)

---

## Installation

1. Cloner le dépôt :
```bash
git clone git@github.com:ton-utilisateurChatbotIA
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


Multi-utilisateur, profils, export du modèle fine-tuné


