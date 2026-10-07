import json
import os
import re

import ollama

from knowledge import (load_knowledge, search_knowledge, format_fragment, format_label, cited_numbers,
                       ensure_citations)
from graph import bridges
from retrieval import HybridRetriever

SYSTEM_PROMPT = """Tu es l'assistant de campagne d'un joueur de jeu de rôle : tu l'aides à retrouver ce que ses notes disent. Réponds toujours en français, de façon concise.
Pour les questions sur l'univers, appuie-toi UNIQUEMENT sur les extraits fournis.
CITATIONS OBLIGATOIRES : chaque phrase qui donne un fait se termine par le numéro de l'extrait qui le contient, par exemple « Kasimir est un elfe du crépuscule [2]. ». Une réponse factuelle sans aucun [n] est incomplète.
Distingue les faits des suppositions : ce qui est marqué (hypothèse), (théorie) ou (à confirmer) n'est PAS un fait établi, dis-le explicitement.
Si les extraits ne contiennent pas la réponse, dis que tu ne sais pas : n'invente rien.
Pour une simple conversation (salutations, remerciements), réponds naturellement."""

PISTE_PROMPT = """Tu es un enquêteur qui aide un joueur de jeu de rôle (pas le MJ) à relier les éléments de ses notes de campagne. Réponds en français.
On te donne des extraits numérotés et des RAPPROCHEMENTS : des paires de fiches que les notes ne relient pas directement mais qui ont des éléments en commun.
Propose 2 à 4 PISTES, chacune fondée sur un rapprochement :
Piste N : une phrase qui formule le lien possible (« ... pourrait être lié à ... »). C'est une HYPOTHÈSE, jamais un fait.
Justification : les éléments communs et les extraits qui la motivent, cités [1], [2]...
À vérifier : une question à poser au MJ ou une observation à faire en jeu.
Règles : n'invente aucun fait absent des extraits ; ne décris pas de cause ou de motivation que les notes n'indiquent pas ; ce qui est marqué (hypothèse), (théorie) ou (à confirmer) reste incertain ; ne répète pas ce que les notes disent déjà ; si aucun rapprochement n'est plausible, dis-le simplement."""


class Chatbot:
    def __init__(self, model="qwen2.5:7b",
                 history_file="chat_history.json",
                 context_turns=3,
                 top_k=6,
                 extra_links=4):

        self.model = model
        self.history_file = history_file
        self.context_turns = context_turns
        self.top_k = top_k
        self.extra_links = extra_links

        self.knowledge_list = load_knowledge()
        self.retriever = HybridRetriever(self.knowledge_list, self._open_vector_store())

        # Chaque message : {"role": "user" | "bot", "kind": "chat" | "search" | "piste", "content": str}
        self.history = []
        self._load_history()


    def _open_vector_store(self):
        """Recherche par sens si possible ; sinon on retombe sur les mots-clés seuls."""
        try:
            from vector_store import VectorStore
            store = VectorStore()
            store.ensure_index(self.knowledge_list)
            return store
        except Exception as e:
            print(f"[avertissement] recherche par sens indisponible, mots-clés seuls ({e})")
            return None


    def _load_history(self):
        if not os.path.exists(self.history_file):
            return
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                self.history = json.load(f)
        except (json.JSONDecodeError, OSError):
            self.history = []


    def _save_history(self):
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)


    def reset_history(self):
        self.history = []
        self._save_history()


    def _add_exchange(self, user_msg, bot_msg, kind):
        self.history.append({"role": "user", "kind": kind, "content": user_msg})
        self.history.append({"role": "bot", "kind": kind, "content": bot_msg})
        self._save_history()


    def respond(self, user_input):
        """Point d'entrée commun : `search <mots>` (recherche), `piste <sujet>` (hypothèses), sinon question."""
        text = user_input.strip()
        lowered = text.lower()
        if lowered.startswith("search "):
            return self.search(text[len("search "):])
        if lowered.startswith("piste "):
            return self.piste(text[len("piste "):])
        return self.generate_response(text)


    def search(self, keyword):
        keyword = keyword.strip()
        results_kn = search_knowledge(keyword, self.knowledge_list)
        if results_kn:
            bot_msg = "Voici ce que j'ai trouvé dans le knowledge :\n" + "\n".join(
                f"- {format_fragment(item)}" for item in results_kn
            )
        else:
            results_history = [
                f"- {m['content']}" for m in self.history
                if m["kind"] == "chat" and keyword.lower() in m["content"].lower()
            ]
            if results_history:
                bot_msg = "Voici ce que j'ai trouvé dans l'historique :\n" + "\n".join(results_history)
            else:
                bot_msg = f"Aucun résultat trouvé pour : {keyword}"

        self._add_exchange(f"search {keyword}", bot_msg, kind="search")
        return bot_msg


    def _build_messages(self, user_input, fragments):
        chat = [m for m in self.history if m["kind"] == "chat"]
        recent = chat[-2 * self.context_turns:] if self.context_turns else []

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += [
            {"role": "user" if m["role"] == "user" else "assistant",
             "content": m["content"].split("\n\nSources :\n")[0]}
            for m in recent
        ]
        messages.append({
            "role": "user",
            "content": f"Extraits de la base de connaissances :\n{self._extracts(fragments)}\n\nQuestion : {user_input}",
        })
        return messages


    @staticmethod
    def _extracts(fragments):
        if not fragments:
            return "(aucun extrait pertinent)"
        return "\n".join(f"[{i}] {format_fragment(f)}" for i, f in enumerate(fragments, 1))


    def _chat(self, messages, temperature):
        """Retourne (réponse, erreur) : une seule des deux valeurs est renseignée."""
        try:
            reply = ollama.chat(
                model=self.model,
                messages=messages,
                options={"temperature": temperature, "num_ctx": 8192},
            )
        except (ConnectionError, ollama.ResponseError) as e:
            return None, f"Erreur Ollama ({e}). Le serveur est-il lancé et le modèle « {self.model} » téléchargé ?"
        return reply["message"]["content"].strip() or "...", None


    @staticmethod
    def _with_sources(response, fragments):
        """Ajoute les fiches réellement citées dans la réponse ([n])."""
        cited = [n for n in cited_numbers(response) if 1 <= n <= len(fragments)]
        if not cited:
            return response
        return response + "\n\nSources :\n" + "\n".join(
            f"[{n}] {format_label(fragments[n - 1])}" for n in cited
        )


    def answer(self, user_input, record=True):
        """Répond et rend aussi les fiches fournies au modèle : {text, fragments, error}.

        `record=False` n'écrit rien dans l'historique (utilisé par l'évaluation).
        """
        fragments = self.retriever.retrieve(user_input, k=self.top_k, extra=self.extra_links)
        response, error = self._chat(self._build_messages(user_input, fragments), temperature=0.3)
        if error:
            return {"text": error, "fragments": fragments, "error": True}
        response = self._with_sources(ensure_citations(response, fragments), fragments)
        if record:
            self._add_exchange(user_input, response, kind="chat")
        return {"text": response, "fragments": fragments, "error": False}


    def generate_response(self, user_input):
        return self.answer(user_input)["text"]


    def _bridge_text(self, indices):
        names = lambda ids: ", ".join(self.knowledge_list[j]["subsection"] for j in ids)
        lines = [
            f"- {self.knowledge_list[a]['subsection']} ↔ {self.knowledge_list[b]['subsection']} : en commun {names(shared)}"
            for _, a, b, shared in bridges(indices, self.retriever.adjacency)
        ]
        return "\n".join(lines) or "(aucun rapprochement calculé)"


    @staticmethod
    def _flag_unsourced(response, n_fragments):
        """Signale les pistes qui ne citent aucune fiche : elles ne sont pas justifiées par les notes."""
        flagged = []
        for block in re.split(r"(?m)^(?=Piste\s*\d*\s*:)", response):
            valid = [n for n in cited_numbers(block) if 1 <= n <= n_fragments]
            if block.lstrip().startswith("Piste") and not valid:
                block = block.rstrip() + "\n(⚠ aucune fiche citée : piste non justifiée par les notes)\n\n"
            flagged.append(block)
        return "".join(flagged)


    def piste(self, subject):
        """Mode enquêteur : propose des liens non écrits, étiquetés hypothèses et sourcés."""
        subject = subject.strip()
        indices = self.retriever.retrieve_indices(subject, k=self.top_k, extra=self.extra_links + 2)
        fragments = [self.knowledge_list[i] for i in indices]
        messages = [
            {"role": "system", "content": PISTE_PROMPT},
            {"role": "user",
             "content": f"Extraits des notes :\n{self._extracts(fragments)}\n\n"
                        f"Rapprochements :\n{self._bridge_text(indices)}\n\nSujet à explorer : {subject}"},
        ]
        response, error = self._chat(messages, temperature=0.3)
        if error:
            return error
        response = self._with_sources(self._flag_unsourced(response, len(fragments)), fragments)
        self._add_exchange(f"piste {subject}", response, kind="piste")
        return response
