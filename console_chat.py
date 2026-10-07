from main import Chatbot


def run():
    bot = Chatbot()

    print("Chatbot IA : Salut ! Commandes : 'search <mot>', 'reset', 'quit'.")

    while True:
        user_input = input("Toi : ").strip()

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Chatbot : À bientôt !")
            break

        if user_input.lower() == "reset":
            bot.reset_history()
            print("Chatbot : Historique effacé.")
            continue

        print("Chatbot :", bot.respond(user_input))


if __name__ == "__main__":
    run()
