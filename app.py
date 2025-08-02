import streamlit as st
from rewrite import rewrite_text
from tts import speak_live_text, generate_audio_file, get_available_voices
import os

st.set_page_config(page_title="EchoVerse – Hugging Face + pyttsx3", layout="wide")

st.title("🎧 EchoVerse – Hugging Face + pyttsx3")
st.caption("Rewrite your text using Hugging Face and speak it with pyttsx3")

# Sidebar Settings
st.sidebar.header("🧠 AI Rewrite Settings")
creativity = st.sidebar.slider("Creativity", 0.1, 1.0, 0.7)
max_tokens = st.sidebar.slider("Max Tokens", 100, 1000, 256)
tone = st.sidebar.selectbox("Tone", ["Neutral", "Happy", "Sad", "Angry"])
voice_name = st.sidebar.selectbox("Voice (pyttsx3)", get_available_voices())
rate = st.sidebar.slider("Voice Rate (speed)", 100, 200, 150)

# Input Area
st.markdown("### 📝 Paste or Type Your Text")
text_input = st.text_area("Input text", height=200)

uploaded_file = st.file_uploader("Or upload a .txt file", type=["txt"])
if uploaded_file:
    text_input = uploaded_file.read().decode("utf-8")

# Main Generate Button
if st.button("🔁 Rewrite + Generate"):
    if not text_input.strip():
        st.error("⚠️ Please enter or upload some text.")
    else:
        with st.spinner("Rewriting text..."):
            rewritten = rewrite_text(text_input, tone=tone, creativity=creativity, max_tokens=max_tokens)
        st.success("✅ Rewriting complete!")

        st.markdown("### ✨ Rewritten Text")
        st.write(rewritten)

        # Live Speech Button
        st.markdown("### 🔊 Speak Live")
        if st.button("🗣️ Speak on My Device"):
            if speak_live_text(rewritten, voice_name=voice_name, rate=rate):
                st.success("🎤 Speaking...")
            else:
                st.error("❌ Could not speak.")

        # File TTS
        with st.spinner("🎧 Generating Audio File..."):
            audio_path = generate_audio_file(rewritten, voice_name=voice_name, rate=rate)

        if audio_path and os.path.exists(audio_path):
            st.success("✅ Audio File Generated")
            st.audio(audio_path)

            with open(audio_path, "rb") as f:
                st.download_button("⬇️ Download Audio", f, file_name="echoverse_output.wav", mime="audio/wav")
        else:
            st.error("❌ Failed to generate audio file.")
