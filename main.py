import json
import os

from transformers import AutoModelForCausalLM, AutoTokenizer

from knowledge import load_knowledge, search_knowledge, format_fragment


class Chatbot:
    def __init__(self, model_name="microsoft/DialoGPT-medium",
                 history_file="chat_history.json",
                 max_new_tokens=100,
                 context_turns=3):

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)

        self.history_file = history_file
        self.max_new_tokens = max_new_tokens
        self.context_turns = context_turns

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


    def _build_prompt_ids(self, user_input):
        """Derniers échanges de chat + nouvelle question, séparés par le token de fin (format DialoGPT)."""
        chat = [m for m in self.history if m["kind"] == "chat"]
        recent = chat[-2 * self.context_turns:]
        text = "".join(m["content"] + self.tokenizer.eos_token for m in recent)
        text += user_input + self.tokenizer.eos_token
        input_ids = self.tokenizer.encode(text, return_tensors="pt")
        return input_ids[:, -800:]  # DialoGPT accepte 1024 tokens, on garde de la place pour la réponse


    def generate_response(self, user_input):
        input_ids = self._build_prompt_ids(user_input)

        output_ids = self.model.generate(
            input_ids,
            attention_mask=input_ids.new_ones(input_ids.shape),
            max_new_tokens=self.max_new_tokens,
            pad_token_id=self.tokenizer.eos_token_id,
            do_sample=True,
            no_repeat_ngram_size=3,
            top_k=100,
            top_p=0.7,
            temperature=0.8
        )

        response = self.tokenizer.decode(
            output_ids[0, input_ids.shape[-1]:],
            skip_special_tokens=True
        ).strip() or "..."

        self._add_exchange(user_input, response, kind="chat")
        return response
