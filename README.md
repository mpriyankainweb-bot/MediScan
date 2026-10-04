# MediScan — English-only clean build

## Kept

- Existing MediScan visual design and layout in `ui_parts.py`
- Gemini medicine-label analysis
- Medicine photo upload
- English microphone input
- Browser-native Listen / Pause / Resume / Stop
- Quick questions
- WhatsApp click-to-chat sharing
- Medical safety rules

## Removed

- Hindi, Telugu, Tamil, Kannada, Malayalam and Marathi UI/voice support
- Language selector and language-switching/re-explanation logic
- Multilingual prompt-building code
- The unused multilingual `languages.py` file

## API key

Create `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "YOUR_REAL_GEMINI_KEY"
```

Do not commit the real key to GitHub.

## Windows

```cmd
cd /d "%USERPROFILE%\Desktop\MediScan_CLEAN"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

If `venv` already exists, just activate it and run `streamlit run app.py`.

## Voice

Microphone transcription uses the browser recording plus Google Web Speech recognition through `SpeechRecognition`, so an internet connection is required. Listen uses the browser's built-in speech synthesis and does not need another API key.
