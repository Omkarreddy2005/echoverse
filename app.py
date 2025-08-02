import streamlit as st
from rewrite import rewrite_text
from tts import generate_audio, speak_text, get_available_voices
import os
import time
import tempfile
from pathlib import Path
import json
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="EchoVerse - Advanced Text Rewriting & TTS", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "EchoVerse - Advanced text rewriting and text-to-speech application"
    }
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 4px;
        border: 1px solid #c3e6cb;
    }
    .warning-message {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.75rem;
        border-radius: 4px;
        border: 1px solid #ffeaa7;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_audio' not in st.session_state:
    st.session_state.current_audio = None
if 'processing_time' not in st.session_state:
    st.session_state.processing_time = {}

# Header
st.markdown("""
<div class="main-header">
    <h1>🎧 EchoVerse - Advanced Text Processing</h1>
    <p>Intelligent text rewriting and high-quality text-to-speech synthesis</p>
</div>
""", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.header("🔧 Configuration")
    
    # Rewriting settings
    st.subheader("✍️ Rewriting Settings")
    creativity = st.slider("Creativity Level", 0.1, 1.0, 0.7, 0.1, 
                          help="Higher values make output more creative but less predictable")
    max_tokens = st.slider("Maximum Output Length", 50, 2000, 512, 50,
                          help="Maximum number of tokens in the rewritten text")
    tone = st.selectbox("Writing Tone", 
                       ["Neutral", "Professional", "Casual", "Academic", "Creative", "Formal"],
                       help="The tone and style for rewriting")
    
    # TTS settings
    st.subheader("🎤 Text-to-Speech Settings")
    
    # Get available voices
    available_voices = get_available_voices()
    voice_options = ["Default"] + [f"{name}" for _, name in available_voices]
    selected_voice = st.selectbox("Voice Selection", voice_options,
                                 help="Choose the voice for audio generation")
    
    speech_rate = st.slider("Speech Rate (WPM)", 50, 300, 180, 10,
                           help="Words per minute - higher is faster")
    
    # Audio format options
    audio_format = st.selectbox("Audio Format", ["WAV", "MP3"], 
                               help="Output audio format")
    
    # Advanced options
    st.subheader("⚙️ Advanced Options")
    auto_play = st.checkbox("Auto-play generated audio", value=True)
    save_history = st.checkbox("Save processing history", value=True)
    show_metrics = st.checkbox("Show performance metrics", value=True)
    
    # Clear history button
    if st.button("🗑️ Clear History"):
        st.session_state.history = []
        st.success("History cleared!")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📝 Input Text")
    
    # Text input options
    input_method = st.radio("Input Method:", 
                           ["Type/Paste Text", "Upload File", "Load from History"],
                           horizontal=True)
    
    text_input = ""
    
    if input_method == "Type/Paste Text":
        text_input = st.text_area("Enter your text here:", 
                                 height=200, 
                                 placeholder="Paste or type your text here...")
        
        # Character counter
        if text_input:
            char_count = len(text_input)
            word_count = len(text_input.split())
            st.caption(f"📊 Characters: {char_count} | Words: {word_count}")
    
    elif input_method == "Upload File":
        uploaded_file = st.file_uploader("Choose a text file", 
                                        type=["txt", "md", "csv"],
                                        help="Supported formats: TXT, MD, CSV")
        if uploaded_file:
            try:
                text_input = uploaded_file.read().decode("utf-8")
                st.text_area("Uploaded content preview:", text_input[:500] + "..." if len(text_input) > 500 else text_input, 
                            height=150, disabled=True)
                st.success(f"✅ File loaded successfully! ({len(text_input)} characters)")
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
    
    elif input_method == "Load from History":
        if st.session_state.history:
            history_options = [f"Entry {i+1}: {item['original'][:50]}..." 
                             for i, item in enumerate(st.session_state.history)]
            selected_history = st.selectbox("Select from history:", history_options)
            if selected_history:
                idx = int(selected_history.split(":")[0].split()[1]) - 1
                text_input = st.session_state.history[idx]['original']
                st.text_area("Selected text:", text_input, height=150, disabled=True)
        else:
            st.info("No history available yet.")

with col2:
    st.markdown("### � Quick Stats")
    
    if text_input:
        # Text analysis
        words = len(text_input.split())
        chars = len(text_input)
        sentences = text_input.count('.') + text_input.count('!') + text_input.count('?')
        estimated_read_time = max(1, words // 200)  # Average reading speed
        estimated_speech_time = max(1, words // (speech_rate / 60))
        
        st.metric("Word Count", words)
        st.metric("Character Count", chars)
        st.metric("Estimated Sentences", sentences)
        st.metric("Est. Reading Time", f"{estimated_read_time} min")
        st.metric("Est. Speech Time", f"{estimated_speech_time:.1f} min")
    else:
        st.info("Enter text to see statistics")

# Processing section
st.markdown("### 🚀 Processing")

# Action buttons
col1, col2, col3, col4 = st.columns(4)

with col1:
    rewrite_only = st.button("✍️ Rewrite Only", disabled=not text_input.strip())
with col2:
    audio_only = st.button("🎤 Audio Only", disabled=not text_input.strip())
with col3:
    rewrite_and_audio = st.button("🔁 Rewrite + Audio", disabled=not text_input.strip())
with col4:
    quick_speak = st.button("📢 Quick Speak", disabled=not text_input.strip())

# Processing logic
if text_input.strip():
    # Validate input length
    if len(text_input) > 10000:
        st.warning("⚠️ Text is quite long. Processing may take some time.")
    
    if rewrite_only or rewrite_and_audio:
        start_time = time.time()
        
        with st.spinner("✍️ Rewriting text..."):
            try:
                rewritten = rewrite_text(text_input, tone=tone, creativity=creativity, max_tokens=max_tokens)
                rewrite_time = time.time() - start_time
                
                if show_metrics:
                    st.session_state.processing_time['rewrite'] = rewrite_time
                
                st.markdown("### ✨ Rewritten Text")
                st.markdown(f"""
                <div class="success-message">
                    <strong>✅ Rewriting completed in {rewrite_time:.2f} seconds</strong>
                </div>
                """, unsafe_allow_html=True)
                
                # Show rewritten text with copy button
                st.text_area("Rewritten content:", rewritten, height=200)
                
                # Save to history
                if save_history:
                    history_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'original': text_input,
                        'rewritten': rewritten,
                        'settings': {
                            'tone': tone,
                            'creativity': creativity,
                            'max_tokens': max_tokens
                        }
                    }
                    st.session_state.history.append(history_entry)
                
                # Generate audio if requested
                if rewrite_and_audio:
                    audio_start_time = time.time()
                    
                    with st.spinner("🎧 Generating audio..."):
                        # Get voice ID if not default
                        voice_id = None
                        if selected_voice != "Default" and available_voices:
                            for vid, vname in available_voices:
                                if vname in selected_voice:
                                    voice_id = vid
                                    break
                        
                        # Generate audio file
                        output_filename = f"echoverse_output_{int(time.time())}.wav"
                        audio_path = generate_audio(rewritten, output_filename, speech_rate, voice_id)
                        audio_time = time.time() - audio_start_time
                        
                        if show_metrics:
                            st.session_state.processing_time['audio'] = audio_time
                        
                        if audio_path and os.path.exists(audio_path):
                            st.session_state.current_audio = audio_path
                            
                            st.markdown("### 🎧 Generated Audio")
                            st.markdown(f"""
                            <div class="success-message">
                                <strong>✅ Audio generated in {audio_time:.2f} seconds</strong>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Audio player
                            st.audio(audio_path, format='audio/wav')
                            
                            # Download button
                            with open(audio_path, "rb") as f:
                                st.download_button(
                                    "⬇️ Download Audio",
                                    f.read(),
                                    file_name=f"echoverse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav",
                                    mime="audio/wav"
                                )
                        else:
                            st.error("❌ Audio generation failed. Check TTS configuration.")
                            
            except Exception as e:
                st.error(f"❌ Error during rewriting: {str(e)}")
                st.exception(e)
    
    elif audio_only:
        audio_start_time = time.time()
        
        with st.spinner("🎧 Generating audio from original text..."):
            try:
                # Get voice ID if not default
                voice_id = None
                if selected_voice != "Default" and available_voices:
                    for vid, vname in available_voices:
                        if vname in selected_voice:
                            voice_id = vid
                            break
                
                output_filename = f"echoverse_original_{int(time.time())}.wav"
                audio_path = generate_audio(text_input, output_filename, speech_rate, voice_id)
                audio_time = time.time() - audio_start_time
                
                if show_metrics:
                    st.session_state.processing_time['audio'] = audio_time
                
                if audio_path and os.path.exists(audio_path):
                    st.session_state.current_audio = audio_path
                    
                    st.markdown("### 🎧 Generated Audio")
                    st.markdown(f"""
                    <div class="success-message">
                        <strong>✅ Audio generated in {audio_time:.2f} seconds</strong>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.audio(audio_path, format='audio/wav')
                    
                    with open(audio_path, "rb") as f:
                        st.download_button(
                            "⬇️ Download Audio",
                            f.read(),
                            file_name=f"echoverse_original_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav",
                            mime="audio/wav"
                        )
                else:
                    st.error("❌ Audio generation failed. Check TTS configuration.")
                    
            except Exception as e:
                st.error(f"❌ Error during audio generation: {str(e)}")
                st.exception(e)
    
    elif quick_speak:
        with st.spinner("📢 Speaking text..."):
            try:
                # Get voice ID if not default
                voice_id = None
                if selected_voice != "Default" and available_voices:
                    for vid, vname in available_voices:
                        if vname in selected_voice:
                            voice_id = vid
                            break
                
                success = speak_text(text_input, speech_rate, voice_id)
                if success:
                    st.success("✅ Text spoken successfully!")
                else:
                    st.error("❌ Failed to speak text.")
                    
            except Exception as e:
                st.error(f"❌ Error during speech: {str(e)}")

# Performance metrics section
if show_metrics and st.session_state.processing_time:
    st.markdown("### 📈 Performance Metrics")
    
    cols = st.columns(len(st.session_state.processing_time))
    for i, (operation, time_taken) in enumerate(st.session_state.processing_time.items()):
        with cols[i]:
            st.metric(f"{operation.title()} Time", f"{time_taken:.2f}s")

# History section
if save_history and st.session_state.history:
    with st.expander("📚 Processing History", expanded=False):
        for i, entry in enumerate(reversed(st.session_state.history[-5:])):  # Show last 5
            st.markdown(f"**Entry {len(st.session_state.history) - i}** - {entry['timestamp'][:19]}")
            st.text(f"Original: {entry['original'][:100]}...")
            st.text(f"Rewritten: {entry['rewritten'][:100]}...")
            st.json(entry['settings'])
            st.markdown("---")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🎧 EchoVerse - Powered by Advanced NLP and TTS Technology</p>
    <p>Built with Streamlit • Enhanced for Performance and User Experience</p>
</div>
""", unsafe_allow_html=True)
