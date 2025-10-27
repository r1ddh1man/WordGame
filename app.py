import streamlit as st
from pathlib import Path
from providers import OnlineWordProvider
from wordgame import WordGame

# ---------- App setup ----------
st.set_page_config(page_title="Word Game Gift", page_icon="💌", layout="centered")
st.title("💌 Word Game — A Gift")
st.markdown("Guess the secret word! Feedback shows how many **unique letters** your guess has in common with the secret. Duplicates count once.")

# ---------- Load engine once ----------
def init_engine(max_attempts: int = 20) -> WordGame:
    engine = WordGame(max_attempts=max_attempts)
    engine.provider = OnlineWordProvider(timeout=5)
    return engine

if "engine" not in st.session_state:
    st.session_state.engine = init_engine(max_attempts=20)

eng: WordGame = st.session_state.engine

# ---------- Sidebar controls ----------
with st.sidebar:
    st.header("Game Controls")
    length = st.number_input("Word length", min_value=3, max_value=15, value=5, step=1)
    attempts = st.number_input("Max attempts", min_value=5, max_value=20, value=20, step=1)
    
    colA, colB = st.columns(2)
    with colA:
        if st.button("🔁 New Game", use_container_width=True):
            # keep same engine (words bucket) but update attempts and start round
            eng.max_attempts = int(attempts)
            try:
                eng.new_game(int(length))
            except ValueError as e:
                st.error(str(e))
            else:
                # st.session_state.last_source = eng.secret_source
                st.rerun()
    with colB:
        if st.button("♻️ Reset Engine", use_container_width=True,
                     help="Reset the engine (online only; no local file)."):
            st.session_state.engine = init_engine(max_attempts=int(attempts))
            # also immediately start a round at chosen length if possible
            try:
                st.session_state.engine.new_game(int(length))
                # st.session_state.last_source = st.session_state.engine.secret_source
            except ValueError:
                pass
            st.rerun()


# ---------- If no active round, prompt to start ----------
if eng.status == "idle" or eng.length is None:
    st.info("Pick a **Word length** in the sidebar and click **New Game** to begin!")
    st.stop()

# ---------- Status metrics ----------
cols = st.columns(3)
cols[0].metric("Status", eng.status.capitalize())
cols[1].metric("Attempts left", eng.attempts_left)
cols[2].metric("Word length", eng.length)

st.divider()

# ---------- Guess input ----------
disabled = eng.status != "playing"
guess = st.text_input(
    "Enter your guess:",
    max_chars=eng.length or 20,
    placeholder=f"{eng.length} letters (A–Z)",
    disabled=disabled,
)
submit = st.button("Guess", type="primary", disabled=disabled)

# ---------- Handle a guess ----------
if submit and eng.status == "playing":
    result = eng.guess(guess)
    if not result.valid:
        st.warning(result.message)
    else:
        st.info(f"**Common letters:** {result.common}")
        # Win/Lose feedback
        if eng.status == "won":
            st.balloons()
            st.success("You found the word! 🎉")
        elif eng.status == "lost":
            st.error("Out of attempts.")

# ---------- History ----------
st.subheader("History")
history = eng.history()
if not history:
    st.caption("No guesses yet.")
else:
    # newest first
    for i, h in enumerate(reversed(history), start=1):
        st.write(f"**#{len(history)-i+1}** — `{h['guess']}` → **{h['common']}** common")

# ---------- End-of-game section ----------
if eng.status in ("won", "lost"):
    st.markdown("---")
    st.write(f"**Secret word:** `{eng.secret}`")
    if st.button("Play Again", use_container_width=True):
        # start another round with same length & attempts
        try:
            eng.new_game(eng.length or 5)
        except ValueError as e:
            st.error(str(e))
        st.rerun()
