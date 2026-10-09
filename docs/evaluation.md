# Évaluation : méthode et historique des mesures

Ce document garde la trace des mesures faites pendant le développement. Règles de lecture :

- Chaque mesure porte sa date (celle du commit) et sa source : le README tel qu'il était à ce commit (`git show <commit>:README.md`).
- Sauf mention contraire, les mesures portent sur **les fiches privées de l'auteur** (non versionnées). Leurs fichiers de résultats (`eval/results_*.json`) sont ignorés par git : seuls les chiffres recopiés dans le README de l'époque sont vérifiables dans le dépôt.
- Le jeu de test, le nombre de fiches et le nombre de passages changent d'une ligne à l'autre : **les lignes ne sont pas strictement comparables**.
- Les réponses sont générées à température 0,3. Deux mesures successives sur des fiches identiques ont donné 96 % puis 95 % pour « hybride + liens » (commit `4501648`) : un écart de 0 à 3 points entre configurations est du bruit.

## Méthode

- **Récupération** (`python eval/eval_retrieval.py`) : pour chaque question, une des fiches attendues doit apparaître dans les k premières. Métriques : hit@k et MRR. Configurations : mots-clés, sens (embeddings), hybride.
- **Réponses** (`python eval/eval_answers.py [--configs a,b] [--repeat N]`) : notation déterministe, sans modèle juge (`eval/scoring.py`).
  - Types de questions : fait (faits attendus), abstention (les notes ne disent rien), incertain (notes contradictoires ou hypothétiques).
  - Critères : faits attendus présents ; faits retrouvés dans les fiches réellement citées ; abstention reconnue ; réserve exprimée ; aucun nom propre absent des fiches fournies (ancrage).
  - Configurations : LLM seul, mots-clés, hybride, hybride + liens (fiches voisines dans le graphe).
- Le jeu d'exemple public (`data/sample_lore/`) sert aux tests et à une démonstration de la méthode ; il est trop petit pour produire des chiffres.

## Récupération

| Date | Commit | Fiches | Questions | Mots-clés | Sens | Hybride |
|---|---|---|---|---|---|---|
| 2026-10-07 | `0c712e6` | 156 | 25 | 88 % | 92 % | 96 % |

hit@6. Mesure **antérieure à l'enrichissement des fiches** (le nombre de fiches est passé de 156 à 192 depuis) : elle n'est pas représentative de l'état actuel et n'a pas été refaite.

Effet du graphe de liens, mesuré au commit `1fe12e3` (2026-10-07) sur 14 questions à deux éléments : 12/14 contre 11/14 pour un même budget de 10 fiches. Jeu trop petit pour conclure.

## Réponses : historique

Colonnes : Faits, Abstention, Incertitude, Ancrage, Global (— : non rapporté). s/rép. : secondes par réponse.

| Date | Commit | Fiches | Questions | Passes | Configuration | Faits | Abstention | Incertitude | Ancrage | Global | s/rép. |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-07 | `5ac75f0` | n.c. | 35 | 1 | LLM seul | 0 % | 40 % | 0 % | 66 % | 6 % | 5,7 |
| | | | | | Mots-clés | 75 % | 80 % | 83 % | 100 % | 77 % | 3,5 |
| | | | | | Hybride | 79 % | 100 % | 67 % | 97 % | 80 % | 3,2 |
| | | | | | Hybride + liens | 88 % | 100 % | 67 % | 100 % | 86 % | 3,9 |
| 2026-10-07 | `5e3df83` | n.c. | 53 | 2 | Hybride | 77/82 | — | — | 98 % | 86 % (90 % notation corrigée) | — |
| | | | | | Hybride + liens | 79/82 | — | — | 99 % | 88 % (92 %) | — |
| 2026-10-07 | `04b9888` | n.c. | 53 | 2 | Hybride | 91 % | — | 60 % | 97 % | 90 % | — |
| | | | | | Hybride + liens | 95 % | — | 90 % | 100 % | 95 % | — |
| 2026-10-08 | `4c91013` | 173 | 69 | 2 | Hybride | 94 % | 94 % | 90 % | 100 % | 93 % | 3,5 |
| | | | | | Hybride + liens | 93 % | 100 % | 100 % | 100 % | 94 % | 4,1 |
| 2026-10-08 | `28108d3` | 180 | 78 | 2 | Hybride | 91 % | 94 % | 70 % | 100 % | 90 % | 3,4 |
| | | | | | Hybride + liens | 96 % | 88 % | 100 % | 100 % | 96 % | 5,0 |
| 2026-10-08 | `4501648` | 190 | 78 | 2 | Hybride | 95 % | 100 % | 80 % | 100 % | 95 % | 4,0 |
| | | | | | Hybride + liens | 95 % | 94 % | 90 % | 100 % | 95 % | 5,1 |
| 2026-10-09 | `dacd66d` | 190 | 104 | 2 | Hybride | 94 % | 88 % | 79 % | 100 % | 92 % | 3,8 |
| | | | | | Hybride + liens | 96 % | 83 % | 86 % | 100 % | 94 % | 5,3 |
| 2026-10-09 | `3781ded` | 192 | 113 | 2 | Hybride | 95 % | 100 % | 86 % | 99 % | 95 % | 4,3 |
| | | | | | Hybride + liens | 98 % | 95 % | 100 % | 100 % | 98 % | 6,6 |

Précisions sur les lignes :

- `5ac75f0` : 24 questions sur des faits, 5 sans réponse dans les notes, 6 aux notes contradictoires ou hypothétiques. Première mesure, avant correction de la notation.
- `5e3df83` : contradictions levées dans les fiches, noms normalisés, citations forcées par le prompt et par un filet de sécurité déterministe. « Notation corrigée » : formules de réserve légitimes ajoutées après coup à `scoring.py` et recalculées sur les réponses déjà obtenues (pas une nouvelle mesure).
- `04b9888` : vérification des citations (`fix_citations`) et lecture des citations groupées `[1, 8]`. Les deux changements ont été faits ensemble : leur part respective n'est pas mesurée.
- `4c91013` : jeu passé de 53 à 69 questions (16 sur les nouveaux contenus), donc non comparable aux lignes précédentes.
- `28108d3` : un premier passage avait donné 92 % pour « hybride + liens » à cause d'une fiche de 6 300 caractères qui débordait le contexte du modèle (8 192 jetons).
- `4501648` : deux corrections de notation (un mot après une citation n'est plus pris pour un nom inventé ; « sans qu'on sache » compte comme réserve), puis mesure refaite sur de nouvelles réponses.
- `dacd66d` : a révélé qu'à une question sans réponse dans les notes, le modèle complétait avec une position plausible.
- `3781ded` : après une phase de questions-réponses avec le joueur pour enrichir les fiches.

## Ce que les échecs ont appris (corrections faites dans les fiches, pas dans le code)

- **Le modèle de 7 milliards de paramètres comble les vides.** Une absence doit être écrite dans la fiche (« non noté »), sinon il invente une réponse plausible et cite une fiche qui n'en parle pas.
- **Une fiche longue est mal lue** : au-delà de quelques milliers de caractères, le contexte déborde et le bot répond « je ne sais pas » à tort. Le fait principal vient en premier.
- **Un personnage mort doit être au passé partout**, avec un statut explicite, sinon une autre fiche au présent le fait réapparaître vivant.
- **Une théorie doit être étiquetée** (hypothèse, à confirmer), sinon elle est présentée comme un fait.
- **Une phrase sans sujet est une mauvaise réponse**, et un mot courant attire des fiches hors sujet.
- **Un nom de fiche trop courant** devient un nœud du graphe qui noie les vrais liens.

## Limites connues de la mesure

- Jeu de test petit, écrit par l'auteur, sur ses propres fiches : risque de mesurer ce qu'on a corrigé.
- Une seule à deux passes à température 0,3 : le bruit entre deux mesures atteint 1 à 2 points.
- Échecs récurrents : réponse correcte mais incomplète, réponse trop courte pour être rattachée à une fiche, réserve légitime non reconnue comme abstention par la notation.
- L'écart entre « hybride » et « hybride + liens » (0 à 3 points) reste dans le bruit.
