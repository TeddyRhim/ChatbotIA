from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os

model_name = "microsoft/DialoGPT-medium"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

print("Chatbot IA : Salut ! Tape 'quit' pour arrêter.")

chat_history_ids = None
history_file = "chat_history.txt"
max_tokens = 500

history_user = []
history_bot = []

# mémoire courte, récupère les 5 derniers messages de l'histo
def get_recent_context(n=5):
    return history_user[-n:], history_bot[-n:]

def search_history(keyword):
    results = []
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            for line in f:
                if keyword.lower() in line.lower():
                    results.append(line.strip())
    return results


# Charger l'historique depuis le fichier
mode = input("Mode de conversation (reset/continue) : ").lower()
if mode == "continue" and os.path.exists(history_file):
    with open(history_file, "r", encoding="utf-8") as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith("Toi : "):
                history_user.append(line.replace("Toi : ", ""))
            elif line.startswith("Chatbot : "):
                history_bot.append(line.replace("Chatbot : ", ""))
elif mode == "reset":
    with open(history_file, "w", encoding="utf-8") as f:
        pass



while True:
    user_input = input("Toi : ")

    if user_input.lower() == "quit":
        print("Chatbot : À bientôt !")
        chat_history_ids = None
        break

    if user_input.lower() in ["!help", "/help"]:
        print("Chatbot : Commandes disponibles :")
        print("- quit → quitter la session")
        print("- reset → effacer l'historique")
        print("- history → afficher l'historique complet")
        print("- search <mot> → chercher un sujet dans l'historique")
        print("- help → afficher cette liste")
        continue

    if user_input.lower() == "reset":
        print("Chatbot : Historique effacé?")
        chat_history_ids = None
        history_user = []
        history_bot = []
        with open(history_file, "w", encoding="utf-8") as f:
            pass
        continue

    if user_input.lower() == "history":
        print("Chatbot : Historique complet :")
        for u, b in zip(history_user, history_bot):
            print(f"Toi : {u}")
            print(f"Chatbot : {b}")
        continue

    if user_input.lower().startswith("search "):
        keyword = user_input[7:]
        results = search_history(keyword)
        if results:
            print("Chatbot : Voici les passages trouvés :")
            for r in results:
                print(r)
        else:
            print(f"Chatbot : Aucun résultat trouvé pour '{keyword}'")
        continue

    history_user.append(user_input)

    recent_users, recent_bots = get_recent_context(n=5)
    context_text = ""
    for u, b in zip(recent_users, recent_bots):
        context_text += f"User: {u} Bot: {b} "
    context_text += f"User: {user_input} Bot:"


    input_ids = tokenizer.encode(user_input + tokenizer.eos_token, return_tensors="pt")

    chat_history_ids = model.generate(
        input_ids,
        max_length=max_tokens,
        pad_token_id=tokenizer.eos_token_id,
        no_repeat_ngram_size=3,
        top_k=100,
        top_p=0.7,
        temperature=0.8
    )

    output = tokenizer.decode(chat_history_ids[:, input_ids.shape[-1]:][0], skip_special_tokens=True)
    print(f"Chatbot : {output}")
    history_bot.append(output)

    with open(history_file, "w", encoding="utf-8") as f:
        for u, b in zip(history_user, history_bot):
            f.write(f"Toi : {u}\n")
            f.write(f"Chatbot : {b}\n")
        if len(history_user) > len(history_bot):
            f.write(f"Toi : {history_user[-1]}\n")
