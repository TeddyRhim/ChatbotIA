from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

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

# Habillage gothique « cathédrale en ruine », entièrement local (aucune police, image ni son téléchargé).
THEME_CSS = """
<style>
:root {
  --noir: #030408;
  --pierre: #0b0d13;
  --pierre-claire: #131620;
  --lune: #b9c6d2;
  --sang: #9b1a28;
  --sang-vif: #c4283a;
  --or: #8a6d3b;
  --or-clair: #b89654;
  --parchemin: #cfd3d8;
  --titre: "Old English Text MT", "UnifrakturCook", "Palatino Linotype", "Book Antiqua", Georgia, serif;
  --texte: "Palatino Linotype", "Book Antiqua", Palatino, Georgia, serif;
}
html, body, [class*="css"], .stMarkdown, p, li, label, input, textarea {
  font-family: var(--texte);
  color: var(--parchemin);
}
::selection { background: var(--sang); color: #fff; }
::-webkit-scrollbar { width: 10px; background: var(--noir); }
::-webkit-scrollbar-thumb { background: #2a1217; border: 1px solid #4a1b24; }

/* Chrome de Streamlit masqué : rien ne doit casser l'ambiance */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }

.stApp {
  background:
    radial-gradient(ellipse at 50% -10%, rgba(90, 14, 24, 0.28) 0, transparent 55%),
    radial-gradient(ellipse at 50% 115%, rgba(110, 16, 26, 0.30) 0, transparent 50%),
    linear-gradient(180deg, #020307 0%, #06080d 55%, #0a0b11 100%);
  background-attachment: fixed;
}
.block-container { max-width: 52rem; position: relative; }
/* Deux colonnes de pierre qui encadrent la page, comme une nef */
.block-container::before, .block-container::after {
  content: ""; position: absolute; top: 0; bottom: 0; width: 1px;
  background: linear-gradient(180deg, transparent, rgba(138, 109, 59, 0.45) 12%, rgba(138, 109, 59, 0.12) 60%, transparent);
}
.block-container::before { left: -1.2rem; }
.block-container::after { right: -1.2rem; }

/* Lune pâle, voilée */
.stApp::before {
  content: ""; position: fixed; top: 34px; right: 6.5%;
  width: 46px; height: 46px; border-radius: 50%;
  background: radial-gradient(circle at 36% 34%, #e9f2f8 0, var(--lune) 55%, #6f8aa0 100%);
  box-shadow: 0 0 36px 10px rgba(185, 198, 210, 0.16);
  opacity: 0.5; pointer-events: none; z-index: 0;
}
/* Vignette très appuyée : on ne voit que ce qu'éclairent les bougies */
.stApp::after {
  content: ""; position: fixed; inset: 0;
  background: radial-gradient(ellipse at center, transparent 30%, rgba(0, 0, 0, 0.62) 70%, rgba(0, 0, 0, 0.94) 100%);
  pointer-events: none; z-index: 3;
}

/* Grande verrière gothique (arc brisé, meneaux, rosace) en filigrane */
.verriere {
  position: fixed; left: 50%; top: 0; width: min(560px, 90vw); height: 100vh; transform: translateX(-50%);
  pointer-events: none; z-index: 0; opacity: 0.20;
  background: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 700' preserveAspectRatio='xMidYMin slice'><g fill='none' stroke='%23a3202f' stroke-width='2'><path d='M40 700V250Q40 70 200 12Q360 70 360 250V700'/><path d='M62 700V255Q62 90 200 40Q338 90 338 255V700'/><path d='M200 40V700M130 700V230M270 700V230M62 400H338'/><circle cx='200' cy='170' r='58'/><circle cx='200' cy='170' r='34'/><path d='M200 112V228M142 170H258M159 129L241 211M241 129L159 211'/><path d='M62 255Q130 230 200 255Q270 230 338 255'/></g></svg>") center top / 100% 100% no-repeat;
  filter: drop-shadow(0 0 14px rgba(155, 26, 40, 0.5));
}
/* Grain de pierre / de vieux papier */
.grain {
  position: fixed; inset: 0; pointer-events: none; z-index: 2; opacity: 0.10; mix-blend-mode: overlay;
  background: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 .7 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");
}

/* Brume qui dérive lentement */
.brume {
  position: fixed; left: -30%; width: 160%; height: 55%;
  pointer-events: none; z-index: 1; opacity: 0.38;
  background:
    radial-gradient(ellipse at 20% 50%, rgba(140, 160, 180, 0.14) 0, transparent 45%),
    radial-gradient(ellipse at 70% 40%, rgba(120, 140, 165, 0.10) 0, transparent 50%);
  filter: blur(18px);
}
.brume.haute { top: 8%; animation: derive 70s linear infinite alternate; }
.brume.basse { bottom: -8%; animation: derive 95s linear infinite alternate-reverse; opacity: 0.55; }
@keyframes derive { from { transform: translateX(-6%); } to { transform: translateX(9%); } }

/* Pluie fine en diagonale */
.pluie {
  position: fixed; inset: -10% 0 0 0; pointer-events: none; z-index: 2; opacity: 0.06;
  background-image: repeating-linear-gradient(105deg, transparent 0 22px, rgba(200, 220, 240, 0.9) 22px 23px);
  background-size: 140px 140px;
  animation: pluie 0.9s linear infinite;
}
@keyframes pluie { from { background-position: 0 0; } to { background-position: -30px 140px; } }

/* Lueur de bougies en bas de l'écran (vacillement lent, sans clignotement brusque) */
.bougies {
  position: fixed; left: 0; right: 0; bottom: 0; height: 30vh; pointer-events: none; z-index: 2;
  background:
    radial-gradient(ellipse 18% 70% at 8% 100%, rgba(214, 120, 40, 0.20) 0, transparent 70%),
    radial-gradient(ellipse 18% 70% at 92% 100%, rgba(214, 120, 40, 0.20) 0, transparent 70%);
  animation: flamme 5.5s ease-in-out infinite;
}
@keyframes flamme { 0%, 100% { opacity: 0.55; } 30% { opacity: 0.9; } 55% { opacity: 0.65; } 80% { opacity: 0.85; } }

/* Éclair à l'ouverture : deux éclats espacés (moins de 3 par seconde), une seule fois par session */
.eclair {
  position: fixed; inset: 0; pointer-events: none; z-index: 9999; opacity: 0;
  background: radial-gradient(ellipse at 78% 0%, rgba(255, 255, 255, 0.95) 0, rgba(190, 215, 255, 0.55) 30%, rgba(120, 150, 210, 0.25) 70%);
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

/* Titre : lettres gothiques si la police existe, sinon petites capitales espacées */
h1 {
  font-family: var(--titre) !important;
  font-weight: 400 !important;
  text-align: center;
  font-size: 3.1rem !important;
  letter-spacing: 0.06em;
  color: #d8dde3 !important;
  text-shadow: 0 0 26px rgba(155, 26, 40, 0.65), 0 2px 0 #000, 0 0 10px rgba(185, 198, 210, 0.15);
  padding: 0.6em 0 0.1em 0 !important;
}
h1 a { display: none; }
.sous-titre {
  text-align: center; font-style: italic; letter-spacing: 0.04em;
  color: #7d8a99; margin: 0 0 0.4em 0;
}
/* Frise sous le titre : filet, losange sanguin, filet */
.ornement {
  height: 22px; margin: 0 auto 1.6em auto; max-width: 30rem;
  background:
    url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 22'><path d='M20 2L30 11L20 20L10 11Z' fill='%239b1a28' stroke='%23b89654' stroke-width='1.2'/><circle cx='20' cy='11' r='2' fill='%23b89654'/></svg>") center / 40px 22px no-repeat,
    linear-gradient(90deg, transparent, rgba(138, 109, 59, 0.75) 40%, transparent 41%, transparent 59%, rgba(138, 109, 59, 0.75) 60%, transparent) center / 100% 1px no-repeat;
}
h2, h3, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
  font-variant: small-caps; letter-spacing: 0.12em; color: var(--or-clair) !important; font-weight: 400 !important;
  border-bottom: 1px solid rgba(138, 109, 59, 0.35); padding-bottom: 0.25em;
}

/* Messages : pierre sombre, double filet doré, tranche sanglante pour les réponses */
[data-testid="stChatMessage"] {
  background: linear-gradient(180deg, rgba(14, 16, 24, 0.93), rgba(8, 9, 14, 0.95));
  border: 1px solid rgba(138, 109, 59, 0.40);
  border-left: 3px solid rgba(138, 109, 59, 0.6);
  border-radius: 0;
  box-shadow: inset 0 0 0 3px #07080d, inset 0 0 0 4px rgba(138, 109, 59, 0.20), 0 8px 26px rgba(0, 0, 0, 0.75);
  padding: 1rem 1.2rem;
}
[data-testid="stChatMessage"]:has(.marque-bot) {
  border-left: 4px solid var(--sang);
  animation: bougie 4.5s ease-in-out infinite;
}
@keyframes bougie {
  0%, 100% { box-shadow: inset 0 0 0 3px #07080d, inset 0 0 0 4px rgba(138, 109, 59, 0.20), 0 8px 26px rgba(0, 0, 0, 0.75), -6px 0 18px rgba(155, 26, 40, 0.20); }
  38%      { box-shadow: inset 0 0 0 3px #07080d, inset 0 0 0 4px rgba(138, 109, 59, 0.20), 0 8px 26px rgba(0, 0, 0, 0.75), -6px 0 26px rgba(155, 26, 40, 0.38); }
  62%      { box-shadow: inset 0 0 0 3px #07080d, inset 0 0 0 4px rgba(138, 109, 59, 0.20), 0 8px 26px rgba(0, 0, 0, 0.75), -6px 0 14px rgba(155, 26, 40, 0.12); }
}
[data-testid="stChatMessage"] p::first-letter { color: var(--parchemin); }
[data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"],
[data-testid="stChatMessage"] img { border-radius: 0 !important; border: 1px solid rgba(138, 109, 59, 0.5); }

[data-testid="stChatInput"] {
  background: rgba(8, 9, 14, 0.96);
  border: 1px solid rgba(138, 109, 59, 0.45);
  border-radius: 0;
  box-shadow: inset 0 0 0 3px #07080d, inset 0 0 0 4px rgba(138, 109, 59, 0.18);
}
[data-testid="stChatInput"] textarea { font-style: italic; }
[data-testid="stChatInput"]:focus-within { border-color: var(--sang-vif); box-shadow: inset 0 0 0 3px #07080d, 0 0 18px rgba(155, 26, 40, 0.5); }
[data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"] { background: transparent !important; }

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #080a10, #040508);
  border-right: 1px solid rgba(138, 109, 59, 0.45);
  box-shadow: 6px 0 24px rgba(0, 0, 0, 0.7);
}
.stButton > button {
  border: 1px solid var(--or);
  background: linear-gradient(180deg, #14090c, #0a0507);
  color: var(--parchemin);
  border-radius: 0;
  letter-spacing: 0.08em;
  font-variant: small-caps;
}
.stButton > button:hover { background: rgba(155, 26, 40, 0.35); border-color: var(--sang-vif); color: #fff; box-shadow: 0 0 14px rgba(155, 26, 40, 0.5); }
[data-testid="stExpander"] {
  background: rgba(5, 6, 10, 0.75);
  border: 1px solid rgba(138, 109, 59, 0.25);
  border-radius: 0;
}
[data-testid="stSlider"] [role="slider"] { background: var(--sang); border: 1px solid var(--or-clair); }
code { background: #14090c !important; color: #d9b98a !important; border: 1px solid rgba(138, 109, 59, 0.25); border-radius: 0; }
.stCaption, [data-testid="stCaptionContainer"] { color: #6f7b89; }
[data-testid="stSpinner"] { color: var(--or-clair); font-style: italic; }
audio { filter: invert(0.88) sepia(0.6) hue-rotate(-20deg) saturate(1.4) brightness(0.8); width: 100%; }

/* Photosensibilité et confort : aucune animation si le système le demande */
@media (prefers-reduced-motion: reduce) {
  .brume, .pluie, .eclair, .bougies, [data-testid="stChatMessage"]:has(.marque-bot) { animation: none !important; }
  .eclair { display: none; }
}
</style>
"""

# Décor : verrière, grain, brume, pluie et bougies en permanence ; l'éclair seulement à la première ouverture.
DECOR_HTML = ('<div class="verriere"></div><div class="grain"></div><div class="brume haute"></div>'
              '<div class="brume basse"></div><div class="pluie"></div><div class="bougies"></div>')
ECLAIR_HTML = '<div class="eclair"></div>'
ORNEMENT_HTML = '<div class="ornement"></div>'


AUDIO_TYPES = {"mp3": "audio/mpeg", "ogg": "audio/ogg", "wav": "audio/wav", "m4a": "audio/mp4"}


def ambiance_file():
    """Musique d'ambiance facultative : assets/ambiance.mp3 (ou .ogg/.wav/.m4a), jamais versionnée."""
    for extension in ("mp3", "ogg", "wav", "m4a"):
        candidate = ASSETS / f"ambiance.{extension}"
        if candidate.exists():
            return candidate
    return None


def set_audio_volume(percent):
    """Règle le lecteur de la barre latérale : volume, boucle, son étouffé et lancement automatique.

    - Le volume et la boucle sont réappliqués à chaque exécution (st.audio n'a pas d'option de volume).
    - Un filtre passe-bas (Web Audio) étouffe la musique, comme entendue à travers un mur.
    - La lecture démarre seule si le navigateur l'autorise ; sinon au premier clic ou à la première touche.
    Le script s'exécute dans une iframe de même origine ; il réessaie un court moment, le temps que
    le lecteur soit affiché.
    """
    components.html(
        f"""<script>
        const volume = {percent} / 100;
        const doc = window.parent.document;
        let essais = 0;
        const preparer = (audio) => {{
          audio.loop = true;
          audio.volume = volume;
          audio.dataset.volume = volume;
          if (audio.dataset.prepare) return;
          audio.dataset.prepare = '1';
          let ctx = null;
          try {{
            const Ctx = window.parent.AudioContext || window.parent.webkitAudioContext;
            ctx = new Ctx();
            const filtre = ctx.createBiquadFilter();
            filtre.type = 'lowpass';
            filtre.frequency.value = 850;
            filtre.Q.value = 0.5;
            ctx.createMediaElementSource(audio).connect(filtre).connect(ctx.destination);
          }} catch (e) {{ ctx = null; }}
          audio.addEventListener('play', () => {{ audio.volume = parseFloat(audio.dataset.volume); }});
          const lancer = () => {{
            if (ctx && ctx.state === 'suspended') ctx.resume();
            if (audio.paused) audio.play().catch(() => {{}});
          }};
          lancer();
          const premier = () => {{
            // léger délai : si le clic visait le bouton lecture du lecteur, on le laisse faire d'abord
            setTimeout(lancer, 150);
            ['click', 'keydown', 'touchstart'].forEach(e => doc.removeEventListener(e, premier, true));
          }};
          ['click', 'keydown', 'touchstart'].forEach(e => doc.addEventListener(e, premier, true));
        }};
        const appliquer = () => {{
          const audio = doc.querySelector('audio');
          if (audio) preparer(audio);
          else if (essais++ < 30) setTimeout(appliquer, 300);
        }};
        appliquer();
        </script>""",
        height=0,
    )


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
st.markdown(ORNEMENT_HTML, unsafe_allow_html=True)

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
        st.audio(str(music), format=AUDIO_TYPES[music.suffix.lstrip('.')], loop=True, autoplay=True)
        volume = st.slider("Volume du fond sonore", 0, 100, 8, key="volume_ambiance")
        set_audio_volume(volume)
        st.caption("La musique démarre seule ; si le navigateur la bloque, elle part au premier clic.")
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
