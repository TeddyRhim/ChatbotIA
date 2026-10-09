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

# Habillage « nuit d'orage », entièrement local (aucune police, image ni son téléchargé).
THEME_CSS = """
<style>
:root {
  --nuit: #07090f;
  --brume: #11161f;
  --lune: #cfe3f0;
  --sang: #b3202e;
  --parchemin: #d6dde6;
}
html, body, [class*="css"], .stMarkdown, p, li {
  font-family: "Palatino Linotype", "Book Antiqua", Palatino, Georgia, serif;
}
.stApp {
  background:
    radial-gradient(circle at 88% 6%, rgba(207, 227, 240, 0.20) 0, rgba(207, 227, 240, 0.05) 7%, transparent 20%),
    radial-gradient(ellipse at 50% 110%, rgba(120, 20, 30, 0.22) 0, transparent 55%),
    linear-gradient(180deg, #05070c 0%, #0a0e16 60%, #10131c 100%);
  background-attachment: fixed;
}
/* Lune pâle, voilée, dans le coin supérieur droit */
.stApp::before {
  content: "";
  position: fixed;
  top: 28px; right: 7.5%;
  width: 54px; height: 54px;
  border-radius: 50%;
  background: radial-gradient(circle at 36% 34%, #f3f9fd 0, var(--lune) 55%, #8fb0c6 100%);
  box-shadow: 0 0 40px 12px rgba(207, 227, 240, 0.22);
  opacity: 0.6;
  pointer-events: none;
  z-index: 0;
}
/* Vignette : les bords de l'écran s'assombrissent, le regard se resserre */
.stApp::after {
  content: "";
  position: fixed; inset: 0;
  background: radial-gradient(ellipse at center, transparent 45%, rgba(0, 0, 0, 0.55) 80%, rgba(0, 0, 0, 0.85) 100%);
  pointer-events: none;
  z-index: 3;
}
header[data-testid="stHeader"] { background: transparent; }

/* Brume qui dérive lentement */
.brume {
  position: fixed; left: -30%; width: 160%; height: 55%;
  pointer-events: none; z-index: 1; opacity: 0.55;
  background:
    radial-gradient(ellipse at 20% 50%, rgba(150, 170, 190, 0.16) 0, transparent 45%),
    radial-gradient(ellipse at 70% 40%, rgba(130, 150, 175, 0.12) 0, transparent 50%);
  filter: blur(18px);
}
.brume.haute { top: 8%; animation: derive 70s linear infinite alternate; }
.brume.basse { bottom: -8%; animation: derive 95s linear infinite alternate-reverse; opacity: 0.7; }
@keyframes derive { from { transform: translateX(-6%); } to { transform: translateX(9%); } }

/* Pluie fine en diagonale, à peine visible */
.pluie {
  position: fixed; inset: -10% 0 0 0; pointer-events: none; z-index: 2; opacity: 0.07;
  background-image: repeating-linear-gradient(105deg, transparent 0 22px, rgba(200, 220, 240, 0.9) 22px 23px);
  background-size: 140px 140px;
  animation: pluie 0.9s linear infinite;
}
@keyframes pluie { from { background-position: 0 0; } to { background-position: -30px 140px; } }

/* Éclair à l'ouverture : deux éclats espacés (moins de 3 par seconde), une seule fois par session */
.eclair {
  position: fixed; inset: 0; pointer-events: none; z-index: 9999; opacity: 0;
  background:
    radial-gradient(ellipse at 78% 0%, rgba(255, 255, 255, 0.95) 0, rgba(190, 215, 255, 0.55) 30%, rgba(120, 150, 210, 0.25) 70%);
  mix-blend-mode: screen;
  animation: eclair 2.6s ease-out 0.5s 1 both;
}
@keyframes eclair {
  0%   { opacity: 0; }
  3%   { opacity: 0.95; }
  9%   { opacity: 0.05; }
  30%  { opacity: 0.7; }
  48%  { opacity: 0; }
  100% { opacity: 0; }
}

h1 {
  font-variant: small-caps;
  letter-spacing: 0.1em;
  color: var(--lune);
  text-shadow: 0 0 22px rgba(179, 32, 46, 0.35), 0 0 14px rgba(207, 227, 240, 0.18);
  border-bottom: 1px solid rgba(179, 32, 46, 0.65);
  padding-bottom: 0.35em;
}
.sous-titre {
  font-style: italic;
  color: #8393a6;
  margin: -0.4em 0 1.4em 0;
}

[data-testid="stChatMessage"] {
  background: rgba(14, 18, 27, 0.88);
  border: 1px solid rgba(207, 227, 240, 0.08);
  border-left: 3px solid rgba(207, 227, 240, 0.35);
  border-radius: 3px;
  box-shadow: 0 6px 22px rgba(0, 0, 0, 0.55);
}
/* Les réponses vacillent comme une bougie */
[data-testid="stChatMessage"]:has(.marque-bot) {
  border-left-color: var(--sang);
  animation: bougie 4.5s ease-in-out infinite;
}
@keyframes bougie {
  0%, 100% { box-shadow: 0 6px 22px rgba(0, 0, 0, 0.55), -4px 0 14px rgba(179, 32, 46, 0.18); }
  38%      { box-shadow: 0 6px 22px rgba(0, 0, 0, 0.55), -4px 0 20px rgba(179, 32, 46, 0.34); }
  62%      { box-shadow: 0 6px 22px rgba(0, 0, 0, 0.55), -4px 0 12px rgba(179, 32, 46, 0.12); }
}
[data-testid="stChatInput"] {
  background: rgba(14, 18, 27, 0.92);
  border: 1px solid rgba(207, 227, 240, 0.2);
  border-radius: 3px;
}
[data-testid="stChatInput"]:focus-within { border-color: var(--sang); box-shadow: 0 0 14px rgba(179, 32, 46, 0.35); }
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0a0d15, #06080d);
  border-right: 1px solid rgba(179, 32, 46, 0.45);
}
.stButton > button {
  border: 1px solid var(--sang);
  background: transparent;
  color: var(--parchemin);
  border-radius: 3px;
}
.stButton > button:hover { background: rgba(179, 32, 46, 0.3); color: #fff; }
[data-testid="stExpander"] {
  background: rgba(7, 9, 15, 0.6);
  border: 1px solid rgba(207, 227, 240, 0.1);
  border-radius: 3px;
}
.stCaption, [data-testid="stCaptionContainer"] { color: #8393a6; }

/* Photosensibilité et confort : aucune animation si le système le demande */
@media (prefers-reduced-motion: reduce) {
  .brume, .pluie, .eclair, [data-testid="stChatMessage"]:has(.marque-bot) { animation: none !important; }
  .eclair { display: none; }
}
</style>
"""

# Décor : brume et pluie en permanence ; l'éclair seulement à la première ouverture de la session.
DECOR_HTML = '<div class="brume haute"></div><div class="brume basse"></div><div class="pluie"></div>'
ECLAIR_HTML = '<div class="eclair"></div>'


def ambiance_file():
    """Musique d'ambiance facultative : assets/ambiance.mp3 (ou .ogg/.wav/.m4a), jamais versionnée."""
    for extension in ("mp3", "ogg", "wav", "m4a"):
        candidate = ASSETS / f"ambiance.{extension}"
        if candidate.exists():
            return candidate
    return None


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
st.markdown(DECOR_HTML, unsafe_allow_html=True)
if not st.session_state.get("eclair_vu"):
    st.markdown(ECLAIR_HTML, unsafe_allow_html=True)
    st.session_state["eclair_vu"] = True
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
    st.subheader("Ambiance sonore")
    music = ambiance_file()
    if music:
        st.audio(str(music), loop=True)
        st.caption("Appuyez sur lecture : le navigateur bloque le son tant qu'on n'a pas cliqué.")
    else:
        st.caption("Déposez un fichier assets/ambiance.mp3 pour activer une musique de fond.")

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
        with st.spinner("Les ombres fouillent vos notes…"):
            reply = bot.respond(prompt)
        render(reply)
