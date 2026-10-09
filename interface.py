from pathlib import Path

import streamlit as st

from main import Chatbot

ASSETS = Path(__file__).parent / "assets"

st.set_page_config(
    page_title="Grimoire de campagne",
    page_icon=str(ASSETS / "icon.png"),
    layout="centered",
)

SOURCES_MARK = "\n\nSources :\n"
USER_AVATAR = str(ASSETS / "avatar_user.png")
BOT_AVATAR = str(ASSETS / "avatar_bot.png")

# Habillage « nuit brumeuse », entièrement local (aucune police ni image téléchargée).
THEME_CSS = """
<style>
:root {
  --nuit: #0b0e16;
  --brume: #141a26;
  --lune: #cfe3f0;
  --sang: #b3202e;
  --parchemin: #dfe6ee;
}
html, body, [class*="css"], .stMarkdown, p, li {
  font-family: "Palatino Linotype", "Book Antiqua", Palatino, Georgia, serif;
}
.stApp {
  background:
    radial-gradient(circle at 88% 6%, rgba(207, 227, 240, 0.30) 0, rgba(207, 227, 240, 0.08) 7%, transparent 22%),
    radial-gradient(ellipse at 50% 108%, rgba(70, 90, 120, 0.35) 0, transparent 55%),
    linear-gradient(180deg, #0b0e16 0%, #101624 70%, #161d2c 100%);
  background-attachment: fixed;
}
/* Lune pâle dans le coin supérieur droit */
.stApp::before {
  content: "";
  position: fixed;
  top: 28px; right: 7.5%;
  width: 54px; height: 54px;
  border-radius: 50%;
  background: radial-gradient(circle at 36% 34%, #f3f9fd 0, var(--lune) 55%, #8fb0c6 100%);
  box-shadow: 0 0 40px 12px rgba(207, 227, 240, 0.28);
  opacity: 0.85;
  pointer-events: none;
  z-index: 0;
}
header[data-testid="stHeader"] { background: transparent; }

h1 {
  font-variant: small-caps;
  letter-spacing: 0.08em;
  color: var(--lune);
  text-shadow: 0 0 18px rgba(207, 227, 240, 0.25);
  border-bottom: 1px solid rgba(179, 32, 46, 0.55);
  padding-bottom: 0.35em;
}
.sous-titre {
  font-style: italic;
  color: #8fa3b8;
  margin: -0.4em 0 1.4em 0;
}

[data-testid="stChatMessage"] {
  background: rgba(20, 26, 38, 0.82);
  border: 1px solid rgba(207, 227, 240, 0.10);
  border-left: 3px solid rgba(207, 227, 240, 0.45);
  border-radius: 4px;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35);
}
[data-testid="stChatMessage"]:has(.marque-bot) {
  border-left-color: var(--sang);
}
[data-testid="stChatInput"] {
  background: rgba(20, 26, 38, 0.9);
  border: 1px solid rgba(207, 227, 240, 0.25);
  border-radius: 4px;
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0f1420, #0b0e16);
  border-right: 1px solid rgba(179, 32, 46, 0.35);
}
.stButton > button {
  border: 1px solid var(--sang);
  background: transparent;
  color: var(--parchemin);
  border-radius: 3px;
}
.stButton > button:hover { background: rgba(179, 32, 46, 0.25); color: #fff; }
[data-testid="stExpander"] {
  background: rgba(11, 14, 22, 0.55);
  border: 1px solid rgba(207, 227, 240, 0.12);
  border-radius: 4px;
}
.stCaption, [data-testid="stCaptionContainer"] { color: #8fa3b8; }
</style>
"""


@st.cache_resource
def get_bot():
    return Chatbot()


def render(content):
    """Affiche une réponse ; le bloc « Sources » est replié pour ne pas alourdir la lecture."""
    answer, _, sources = content.partition(SOURCES_MARK)
    st.markdown('<span class="marque-bot"></span>', unsafe_allow_html=True)  # repère CSS : bordure cramoisie
    st.markdown(answer)
    if sources.strip():
        with st.expander("Sources"):
            st.markdown(sources)


st.markdown(THEME_CSS, unsafe_allow_html=True)
bot = get_bot()

st.title("Grimoire de campagne")
st.markdown('<p class="sous-titre">Interrogez vos notes de campagne. Chaque réponse cite ses sources.</p>',
            unsafe_allow_html=True)

with st.sidebar:
    st.subheader("Commandes")
    st.markdown(
        "- une question en langage naturel\n"
        "- `search mots` : fiches contenant tous les mots\n"
        "- `piste sujet` : hypothèses à vérifier, étiquetées"
    )
    if st.button("Effacer l'historique"):
        bot.reset_history()
        st.rerun()

for msg in bot.history:
    is_user = msg["role"] == "user"
    with st.chat_message("user" if is_user else "assistant", avatar=USER_AVATAR if is_user else BOT_AVATAR):
        if is_user:
            st.markdown(msg["content"])
        else:
            render(msg["content"])

if prompt := st.chat_input("Posez une question à vos notes…"):
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("Les pages se tournent…"):
            reply = bot.respond(prompt)
        render(reply)
