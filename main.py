import json
import os

import ollama

from knowledge import load_knowledge, search_knowledge, retrieve, format_fragment, format_label

SYSTEM_PROMPT = """Tu es l'assistant de campagne d'un joueur de jeu de rôle : tu l'aides à retrouver ce que ses notes disent. Réponds toujours en français, de façon concise.
Pour les questions sur l'univers, appuie-toi UNIQUEMENT sur les extraits fournis et cite ceux que tu utilises avec [1], [2]...
Distingue les faits des suppositions : ce qui est marqué (hypothèse), (théorie) ou (à confirmer) n'est PAS un fait établi, dis-le explicitement.
Si les extraits ne contiennent pas la réponse, dis que tu ne sais pas : n'invente rien.
Pour une simple conversation (salutations, remerciements), réponds naturellement."""


class Chatbot:
    def __init__(self, model="qwen2.5:7b",
                 history_file="chat_history.json",
                 context_turns=3,
                 top_k=6):

        self.model = model
        self.history_file = history_file
        self.context_turns = context_turns
        self.top_k = top_k

        self.knowledge_list = load_knowledge()

        # Chaque message : {"role": "user" | "bot", "kind": "chat" | "search", "content": str}
        self.history = []
        self._load_history()


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
        """Point d'entrée commun : `search <mot>` interroge le knowledge, le reste va au modèle."""
        text = user_input.strip()
        if text.lower().startswith("search "):
            return self.search(text[len("search "):])
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
        recent = chat[-2 * self.context_turns:]

        if fragments:
            extracts = "\n".join(f"[{i}] {format_fragment(f)}" for i, f in enumerate(fragments, 1))
        else:
            extracts = "(aucun extrait pertinent)"

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += [
            {"role": "user" if m["role"] == "user" else "assistant",
             "content": m["content"].split("\n\nSources :\n")[0]}
            for m in recent
        ]
        messages.append({
            "role": "user",
            "content": f"Extraits de la base de connaissances :\n{extracts}\n\nQuestion : {user_input}",
        })
        return messages


    def generate_response(self, user_input):
        fragments = retrieve(user_input, self.knowledge_list, k=self.top_k)

        try:
            reply = ollama.chat(
                model=self.model,
                messages=self._build_messages(user_input, fragments),
                options={"temperature": 0.3, "num_ctx": 6144},
            )
        except (ConnectionError, ollama.ResponseError) as e:
            return f"Erreur Ollama ({e}). Le serveur est-il lancé et le modèle « {self.model} » téléchargé ?"

        response = reply["message"]["content"].strip() or "..."

        if fragments:
            response += "\n\nSources :\n" + "\n".join(
                f"[{i}] {format_label(f)}" for i, f in enumerate(fragments, 1)
            )

        self._add_exchange(user_input, response, kind="chat")
        return response
