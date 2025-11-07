# Chatbot IA - DialoGPT personnalisé

Un chatbot Python basé sur **DialoGPT-medium**, avec historique, mémoire partielle et possibilité de spécialisation via fine-tuning léger (LoRA/PEFT).  
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

ROAD MAP :

✅ Étapes réalisées

Mise en place de l’environnement

Python 3.11, venv, dépendances

Chatbot fonctionnel

DialoGPT-medium opérationnel avec boucle de dialogue

Historique et persistance

Sauvegarde automatique, reset, lecture de l’historique

Mode “Continue”

Reprise de conversation avec contexte limité

Mode “Search” et commandes

Recherche dans l’historique, commandes /help, /quit, /continue

⚙️ Étape en cours

Création et automatisation du savoir

Nettoyage et organisation automatique des données brutes

Génération d’un dataset JSON prêt pour le fine-tuning

🔜 Étapes à venir

Fine-tuning léger (LoRA / PEFT)

Spécialisation du chatbot sur l’univers choisi

Modularisation du code

Organisation propre des scripts et modules

Interface utilisateur

Console améliorée ou interface web pour meilleure expérience

Mémoire externe / RAG

Consultation dynamique d’une base de connaissance

Optimisation & extension

Multi-utilisateur, profils, export du modèle fine-tuné


