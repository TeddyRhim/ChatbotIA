import streamlit as st

from main import Chatbot

st.set_page_config(page_title="Chatbot IA", page_icon="🤖", layout="wide")


@st.cache_resource
def get_bot():
    return Chatbot()


bot = get_bot()

st.title("🤖 Chatbot IA – Interface Web")

if st.sidebar.button("Effacer l'historique"):
    bot.reset_history()
    st.rerun()

for msg in bot.history:
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        st.markdown(msg["content"])

if prompt := st.chat_input("Message (ou « search mot » pour interroger le knowledge)"):
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Réflexion..."):
            reply = bot.respond(prompt)
        st.markdown(reply)
