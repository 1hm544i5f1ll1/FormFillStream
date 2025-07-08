import streamlit as st
import openai
from gtts import gTTS
import soundfile as sf
import numpy as np
import tempfile
import os
import whisper

# App title
st.title("Audio Translator")

# Settings
openai_api_key = st.text_input("OpenAI API Key", type="password")
target_language = st.selectbox("Target Language", ["en", "es", "fr", "de", "it", "ja", "zh"])

# Audio upload
uploaded_file = st.file_uploader("Upload an audio file", type=["wav", "mp3"])

if uploaded_file and openai_api_key:
    # Save uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        audio_path = tmp_file.name
    
    st.audio(audio_path)
    
    if st.button("Translate"):
        with st.spinner("Processing..."):
            try:
                # Transcribe with Whisper
                model = whisper.load_model("base")
                result = model.transcribe(audio_path)
                original_text = result["text"]
                
                # Translate with OpenAI
                openai.api_key = openai_api_key
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": f"Translate to {target_language}"},
                        {"role": "user", "content": original_text}
                    ]
                )
                translated_text = response.choices[0].message.content
                
                # Convert to speech
                tts = gTTS(translated_text, lang=target_language)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    tts.save(tmp.name)
                    st.audio(tmp.name)
                    st.success("Translation complete!")
                    st.write("Original:", original_text)
                    st.write("Translated:", translated_text)
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Clean up
if 'audio_path' in locals():
    try:
        os.unlink(audio_path)
    except:
        pass