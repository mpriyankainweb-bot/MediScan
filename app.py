import base64
import hashlib
import io
import json
import re
from datetime import date
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types

from prompts import (
    DEFAULT_PHOTO_QUESTION,
    SUMMARY_REQUEST_PROMPT,
    SYSTEM_PROMPT,
)
from ui_parts import (
    answer_card_html,
    css,
    esc,
    hero_html,
    qchip_html,
    section_html,
    tracker_html,
    tracker_states,
)

MODEL_NAME = "gemini-3.5-flash-lite"

# English-only UI. The multilingual selector and translation layer have been
# removed, but the existing visual design in ui_parts.py is kept unchanged.
UI = {
    "step1": "📷 Step 1: Take or upload a photo of the medicine",
    "step2": "🔎 Step 2: Find out about the medicine",
    "step3": "🎤 Step 3: Ask a question",
    "identify": "🔎 Identify medicine",
    "listen": "🔊 Listen",
    "pause": "⏸ Pause",
    "resume": "▶ Resume",
    "stop": "⏹ Stop",
    "listen_full": "🔊 Listen to explanation",
    "explanation": "📝 Explanation",
    "voice_step": "🎤 Ask a question by voice - tap the microphone and speak",
    "quick_title": "👆 Or tap a question",
    "q1": "What is this medicine for?",
    "q2": "How should I take it?",
    "q3": "When should I take it?",
    "q4": "What are the side effects?",
    "q5": "Can I take it after food?",
    "q6": "What should I be careful about?",
    "q7": "Is this medicine expired?",
    "q8": "What is this medicine called?",
    "reading": "Reading the label...",
    "thinking": "Finding the answer...",
    "listening": "Understanding your voice...",
    "placeholder": "Type a question here, or attach a photo of the medicine",
    "send_whatsapp": "📤 Send to WhatsApp",
    "open_whatsapp": "📲 Open WhatsApp",
    "disclaimer": "⚠️ General information only - not medical advice. Always confirm with a doctor or pharmacist.",
    "hero_tag": "Scan your medicine and understand it clearly.",
    "greet": "Hello",
    "tr_photo": "Photo",
    "tr_identify": "Identify",
    "tr_ask": "Ask",
    "browse": "📷 Choose photo",
    "drop_hint": "Tap the box to take a photo or pick one from your phone.",
    "scan_another": "📷 Scan another medicine",
    "back_results": "↩ Back to my medicine",
    "earlier": "Earlier answers",
    "wa_ready": "Your summary is ready. Tap the green button, check the message in WhatsApp, then press Send yourself.",
    "ask_locked": "Identify a medicine first, then you can ask questions here.",
    "mic_help": "If the microphone does not work, allow microphone access in your browser (tap the 🔒 icon near the address bar), or type your question below.",
    "voice_tap": "Tap the microphone to speak",
    "voice_sub": "Speak your question, then stop the recording.",
    "voice_missing": "No browser voice was found. You can still read the answer.",
}

def ui(key):
    return UI[key]

ENGLISH_INSTRUCTION = (
    "[Reply only in simple English. Keep medicine names, brand names, active ingredients, "
    "numbers and dates exactly as printed. If something cannot be read from the image, "
    "say clearly that it cannot be determined. Never guess dosage or timing.]\n\n"
)
QUICK_QUESTIONS_EN = {f"q{i}": UI[f"q{i}"] for i in range(1, 9)}

st.set_page_config(page_title="MediScan", page_icon="💊", layout="centered")


# ---------------------------------------------------------------------------
# Secrets (never printed, never shown in the UI)
# ---------------------------------------------------------------------------
def get_secret(name):
    """Return a secret, or None if it is missing / still the example placeholder."""
    try:
        value = str(st.secrets[name]).strip()
    except Exception:
        return None
    if not value or value.lower().startswith("your-"):
        return None
    return value


GEMINI_API_KEY = get_secret("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.title("💊 MediScan")
    st.error(
        "MediScan is not set up yet: the Gemini API key is missing. "
        "Add GEMINI_API_KEY to .streamlit/secrets.toml (see secrets.toml.example) "
        "and restart the app."
    )
    st.stop()


@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()


# ---------------------------------------------------------------------------
# Friendly errors
# ---------------------------------------------------------------------------
NETWORK_WORDS = (
    "getaddrinfo", "connecterror", "connection", "timed out", "timeout",
    "network", "name resolution", "unreachable", "ssl", "max retries",
)


def friendly_error(error):
    """Turn an exception into a short, safe message (never includes keys)."""
    text = str(error).lower()
    code = getattr(error, "code", None)
    if "api key" in text or "api_key" in text or code in (401, 403):
        return (
            "MediScan could not sign in to Gemini. The API key may be wrong or "
            "not allowed. Please check the key in your secrets file."
        )
    if code == 429 or "resource_exhausted" in text or "quota" in text:
        return "Gemini is busy or its free limit was reached. Please wait a minute and try again."
    if any(word in text for word in NETWORK_WORDS):
        return "There is a problem with the internet connection. Please check it and try again."
    if "safety" in text or "blocked" in text:
        return "Gemini could not answer that. Please try a clearer photo or a different question."
    return "Something went wrong while getting the answer. Please try again."


def ask_gemini(parts):
    """Send one request to the existing Gemini chat."""
    if "chat" not in st.session_state:
        return None, "MediScan is not ready yet. Please refresh the page and try again."
    try:
        reply = st.session_state.chat.send_message(parts).text
    except Exception as error:
        return None, friendly_error(error)
    if not reply or not reply.strip():
        return None, "Gemini did not give an answer. Please try a clearer photo or ask again."
    return reply.strip(), None


def transcribe_audio(audio_bytes):
    """Speech -> text using the lightweight Google Speech Recognition endpoint.

    The microphone recording itself comes from Streamlit's native audio_input
    widget (16 kHz WAV). This keeps Gemini out of the speech-to-text path.
    """
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        # Keep speech recognition from hanging forever on a network problem.
        recognizer.operation_timeout = 15
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio = recognizer.record(source)
        # Google Web Speech recognition is used only for transcription.
        # It does not require a Gemini call or a separate API key.
        text = recognizer.recognize_google(
            audio,
            language="en-IN",
            show_all=False,
        )
        text = (text or "").strip()
    except ImportError:
        return None, "Speech recognition is not installed. Run: pip install SpeechRecognition"
    except Exception as error:
        # SpeechRecognition exposes UnknownValueError and RequestError; avoid
        # leaking implementation details into the UI.
        if error.__class__.__name__ == "UnknownValueError":
            return None, "I could not understand the recording. Please speak clearly and try again."
        if error.__class__.__name__ == "WaitTimeoutError":
            return None, "Speech recognition took too long. Please try again or type your question."
        msg = str(error).lower()
        if error.__class__.__name__ == "RequestError" or any(
            word in msg for word in ("request", "network", "connection", "timed out")
        ):
            return None, "Speech recognition needs an internet connection. You can type your question below."
        return None, "I could not understand the recording. Please try again or type your question below."
    except Exception as error:
        msg = str(error).lower()
        if "request" in msg or "network" in msg or "connection" in msg or "timed out" in msg:
            return None, "Speech recognition needs an internet connection. You can type your question below."
        return None, "I could not understand the recording. Please try again or type your question below."
    if not text:
        return None, "I could not hear a question. Please try again or type your question below."
    return text, None


# ---------------------------------------------------------------------------
# Text to speech: browser-native SpeechSynthesis (no API call, no gTTS wait)
# ---------------------------------------------------------------------------
def speech_text(text):
    """Turn the plain answer into browser-friendly speech text."""
    text = re.sub(r"[`*_#]", "", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def show_browser_tts(text):
    """Render an instant, browser-native voice player.

    No audio file is generated and no network TTS request is made. The browser
    uses the browser English (India) voice when one is installed/available.
    """
    lang_tag = "en-IN"
    spoken = speech_text(text)
    payload = json.dumps(spoken[:5000], ensure_ascii=False).replace("</", "<\\/")
    label = ui("listen")
    pause = ui("pause")
    resume = ui("resume")
    stop = ui("stop")
    voice_missing = ui("voice_missing")
    html_page = f"""
    <style>
      body{{margin:0;font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:transparent}}
      .player{{background:#fff;border:2px solid #0F2A3D;border-radius:22px;padding:12px}}
      .row{{display:flex;gap:8px;flex-wrap:wrap}}
      button{{border:2px solid #0F2A3D;border-radius:999px;background:#fff;padding:10px 16px;
              font-weight:800;font-size:15px;cursor:pointer;box-shadow:0 3px 0 #0F2A3D}}
      button.primary{{background:#00957F;color:#fff;border-color:#006F5F;box-shadow:0 3px 0 #006F5F}}
      button:active{{transform:translateY(3px);box-shadow:none}}
      .status{{font-size:13px;color:#3B5A6E;margin-top:9px;min-height:18px}}
    </style>
    <div class="player">
      <div class="row">
        <button class="primary" id="speak">🔊 {esc(label)}</button>
        <button id="pause">⏸ {esc(pause)}</button>
        <button id="resume">▶ {esc(resume)}</button>
        <button id="stop">⏹ {esc(stop)}</button>
      </div>
      <div class="status" id="status"></div>
    </div>
    <script>
      const text={payload};
      const lang={json.dumps(lang_tag)};
      const status=document.getElementById("status");
      let utterance=null;
      function pickVoice() {{
        const voices=window.speechSynthesis.getVoices();
        const exact=voices.find(v => v.lang && v.lang.toLowerCase() === lang.toLowerCase());
        const prefix=voices.find(v => v.lang && v.lang.toLowerCase().startsWith(lang.slice(0,2).toLowerCase()));
        return exact || prefix || null;
      }}
      function speak() {{
        window.speechSynthesis.cancel();
        utterance=new SpeechSynthesisUtterance(text);
        utterance.lang=lang;
        const v=pickVoice();
        if(v) utterance.voice=v;
        status.textContent=v ? "" : {json.dumps(voice_missing)};
        utterance.onstart=()=>status.textContent="";
        utterance.onerror=()=>status.textContent={json.dumps(voice_missing)};
        window.speechSynthesis.speak(utterance);
      }}
      document.getElementById("speak").onclick=speak;
      document.getElementById("pause").onclick=()=>window.speechSynthesis.pause();
      document.getElementById("resume").onclick=()=>window.speechSynthesis.resume();
      document.getElementById("stop").onclick=()=>{{window.speechSynthesis.cancel();status.textContent="";}};
      if ("speechSynthesis" in window) {{
        window.speechSynthesis.onvoiceschanged=()=>{{}};
      }} else {{
        status.textContent={json.dumps(voice_missing)};
        document.querySelectorAll("button").forEach(b=>b.disabled=true);
      }}
    </script>
    """
    components.html(html_page, height=155)


def render_audio_controls(message, index, is_latest):
    if not (is_latest or index in st.session_state.audio_open):
        if st.button(ui("listen_full"), key=f"listen_{index}", use_container_width=True):
            st.session_state.audio_open.add(index)
            st.rerun()
        return
    show_browser_tts(message["content"])

# ---------------------------------------------------------------------------
# Look & feel (all styling lives in ui_parts.py)
# ---------------------------------------------------------------------------
def inject_css():
    st.markdown(css(ui("browse")), unsafe_allow_html=True)


def scroll_to_top():
    """Jump back to the top of the page when the screen changes."""
    components.html(
        "<script>try{var d=window.parent.document;"
        "var m=d.querySelector('[data-testid=\"stMain\"]')||d.querySelector('section.main');"
        "if(m){m.scrollTo({top:0,behavior:'smooth'});}window.parent.scrollTo(0,0);}catch(e){}</script>",
        height=0,
    )


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def add_message(role, kind, content, **extra):
    st.session_state.messages.append({"role": role, "kind": kind, "content": content, **extra})


def make_thumb(data, size=160):
    """Tiny JPEG (base64) of the medicine photo for the answer card."""
    try:
        from PIL import Image, ImageOps

        image = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
        image.thumbnail((size, size))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=80)
        return base64.b64encode(buffer.getvalue()).decode("ascii")
    except Exception:
        return None


def find_thumb(messages, upto):
    for i in range(upto, -1, -1):
        if messages[i]["kind"] == "image":
            return messages[i].get("thumb")
    return None


def file_key(uploaded):
    return getattr(uploaded, "file_id", None) or hashlib.sha1(uploaded.getvalue()).hexdigest()



# Free WhatsApp "click to chat" link: https://wa.me/<number>?text=<message>.
# It only OPENS WhatsApp with the message typed in - the user presses Send.
# Very long links can fail, so the message is shortened to stay under this size
# (measured after URL-encoding; Indian scripts take about 9 characters per letter).
MAX_ENCODED_LENGTH = 4000


def build_whatsapp_share(number, user_name, summary, disclaimer):
    """Returns (url, message_text, was_shortened)."""
    summary = (summary or "").strip() or "No medicine summary available."
    header = f"💊 MediScan - {user_name}\n\n"
    footer = f"\n\n{disclaimer}"
    shortened = False
    while len(quote(header + summary + footer, safe="")) > MAX_ENCODED_LENGTH and len(summary) > 20:
        summary = summary[: int(len(summary) * 0.9)].rstrip()
        shortened = True
    if shortened:
        summary += "..."
    message = header + summary + footer
    digits = re.sub(r"\D", "", number or "")
    target = digits if 8 <= len(digits) <= 15 else ""
    return f"https://wa.me/{target}?text={quote(message, safe='')}", message, shortened


def looks_like_image(data):
    if not data:
        return False
    try:
        from PIL import Image

        Image.open(io.BytesIO(data)).verify()
        return True
    except ImportError:
        return True  # cannot check; let Gemini decide
    except Exception:
        return False


def photo_mime(photo):
    mime = getattr(photo, "type", None)
    if mime in ("image/jpeg", "image/png"):
        return mime
    return "image/png" if (photo.name or "").lower().endswith(".png") else "image/jpeg"


def submit_question(question, display=None, photo_bytes=None, mime=None):
    """Send one question (and optionally a photo) to Gemini in English.

    Messages are stored only when Gemini answers, so the screen and Gemini's own
    memory of the chat never get out of step. Returns True on success.
    """
    parts = []
    if photo_bytes:
        parts.append(types.Part.from_bytes(data=photo_bytes, mime_type=mime))
    parts.append(ENGLISH_INSTRUCTION + question)
    with st.spinner(ui("reading") if photo_bytes else ui("thinking")):
        answer, error = ask_gemini(parts)
    if error:
        message = error
        if display:
            message += f'\n\nYour question was: "{display}"'
        st.session_state.notice = message
        return False
    if photo_bytes:
        add_message("user", "image", photo_bytes, thumb=make_thumb(photo_bytes))
        st.session_state.photo_sent = True
    else:
        st.session_state.asked = True
    if display:
        add_message("user", "text", display)
    add_message("assistant", "text", answer, speakable=True)
    return True


# ---------------------------------------------------------------------------
# Pieces of the screen
# ---------------------------------------------------------------------------
QUICK_ICONS = {"q1": "💊", "q2": "🥄", "q3": "⏰", "q4": "⚠️", "q5": "🍽️", "q6": "🛑", "q7": "📅", "q8": "🏷️"}


def tracker_for(photo_ready, identified, asked):
    """Compact progress strip: photo -> identify -> ask."""
    states = tracker_states([photo_ready, identified, identified and asked])
    icons = ["📷", "🔎", "🎤"]
    labels = [ui("tr_photo"), ui("tr_identify"), ui("tr_ask")]
    return tracker_html(list(zip(icons, labels, states)))


def render_share():
    """WhatsApp: the same free wa.me link as before - the user presses Send."""
    if st.button(ui("send_whatsapp"), use_container_width=True, key="send_whatsapp"):
        with st.spinner("Writing your summary..."):
            summary, summary_error = ask_gemini([ENGLISH_INSTRUCTION + SUMMARY_REQUEST_PROMPT])
        if summary_error:
            st.session_state.pop("wa_share", None)
            st.error(f"Couldn't write the summary: {summary_error}")
        else:
            url, message, shortened = build_whatsapp_share(
                st.session_state.whatsapp_number,
                st.session_state.name,
                summary,
                ui("disclaimer"),
            )
            st.session_state.wa_share = {
                "url": url, "text": message, "shortened": shortened,
            }
    share = st.session_state.get("wa_share")
    if share:
        st.success(ui("wa_ready"))
        st.link_button(ui("open_whatsapp"), share["url"], type="primary", use_container_width=True)
        if share["shortened"]:
            st.warning("The summary was shortened so the WhatsApp link would work. Copy the full text below if you need all of it.")
        st.code(share["text"], language=None, wrap_lines=True)  # has a copy button


# ---------------------------------------------------------------------------
# Screen 1: take a photo and identify
# ---------------------------------------------------------------------------
def render_scan_view(tracker_slot):
    if st.session_state.photo_sent:
        if st.button(ui("back_results"), key="back_results", use_container_width=True):
            st.session_state.view = "result"
            st.session_state.scroll_top = True
            st.rerun()

    with st.container(key="scan_card"):
        st.markdown(section_html(ui("step1")), unsafe_allow_html=True)
        st.markdown(f'<div class="hint">{esc(ui("drop_hint"))}</div>', unsafe_allow_html=True)
        photo_file = st.file_uploader(
            ui("step1"),
            type=["jpg", "jpeg", "png"],
            key=f"photo_uploader_{st.session_state.uploader_n}",
            label_visibility="collapsed",
        )
        if photo_file is not None:
            st.image(photo_file, width=260)

    tracker_slot.markdown(
        tracker_for(photo_file is not None, False, False), unsafe_allow_html=True
    )

    with st.container(key="go_card"):
        st.markdown(section_html(ui("step2")), unsafe_allow_html=True)
        already_done = photo_file is not None and st.session_state.analyzed_file == file_key(photo_file)
        identify_clicked = st.button(
            ui("identify"),
            key="identify",
            type="primary",
            use_container_width=True,
            disabled=photo_file is None or already_done,
        )
        st.caption(ui("ask_locked"))

    if identify_clicked and photo_file is not None:
        photo_bytes = photo_file.getvalue()
        if not looks_like_image(photo_bytes):
            st.session_state.notice = (
                "That file could not be opened as a photo. Please take a new, clear "
                "photo of the medicine and upload it again."
            )
        elif submit_question(DEFAULT_PHOTO_QUESTION, photo_bytes=photo_bytes, mime=photo_mime(photo_file)):
            st.session_state.analyzed_file = file_key(photo_file)
            st.session_state.view = "result"
            st.session_state.asked = False
            st.session_state.scroll_top = True
        st.rerun()


# ---------------------------------------------------------------------------
# Screen 2: the answer, listen, ask by voice, share
# ---------------------------------------------------------------------------
def render_result_view(tracker_slot):
    tracker_slot.markdown(
        tracker_for(True, True, st.session_state.asked), unsafe_allow_html=True
    )

    messages = st.session_state.messages
    speakable = [i for i, m in enumerate(messages) if m.get("speakable")]
    latest = speakable[-1]
    start = latest
    while start > 0 and messages[start - 1]["role"] == "user":
        start -= 1
    question = next((m["content"] for m in messages[start:latest] if m["kind"] == "text"), None)

    st.markdown(
        answer_card_html(
            messages[latest]["content"],
            ui("explanation"),
            ui("disclaimer"),
            thumb_b64=find_thumb(messages, latest),
            question=question,
        ),
        unsafe_allow_html=True,
    )
    render_audio_controls(messages[latest], latest, True)

    with st.container(key="share_card"):
        render_share()
        if st.button(ui("scan_another"), key="scan_another", use_container_width=True):
            st.session_state.view = "scan"
            st.session_state.uploader_n += 1
            st.session_state.scroll_top = True
            st.rerun()

    with st.container(key="ask_card"):
        st.markdown(section_html(ui("voice_step")), unsafe_allow_html=True)
        st.markdown(
            f'<div class="voice-hub"><div class="voice-orb">🎤</div>'
            f'<div class="voice-title">{esc(ui("voice_tap"))}</div>'
            f'<div class="voice-sub">{esc(ui("voice_sub"))}</div></div>',
            unsafe_allow_html=True,
        )
        if hasattr(st, "audio_input"):
            voice = st.audio_input(
                ui("voice_step"),
                sample_rate=16000,
                key=f"voice_{st.session_state.voice_counter}",
                label_visibility="collapsed",
            )
        else:
            voice = None
            st.info("Voice input needs a newer Streamlit. Run: pip install -U streamlit")
        st.caption(ui("mic_help"))

        st.markdown(f"**{ui('quick_title')}**")
        quick = None
        with st.container(key="quick"):
            quick_cols = st.columns(2)
            for n in range(1, 9):
                label_key = f"q{n}"
                with quick_cols[(n - 1) % 2]:
                    if st.button(
                        f"{QUICK_ICONS[label_key]} {ui(label_key)}",
                        key=f"quick_{n}",
                        use_container_width=True,
                    ):
                        quick = (ui(label_key), QUICK_QUESTIONS_EN[label_key])

    if quick:
        submit_question(quick[1], display=quick[0])
        st.rerun()

    if voice is not None:
        voice_bytes = voice.getvalue()
        digest = hashlib.sha1(voice_bytes).hexdigest()
        if digest != st.session_state.last_audio:
            st.session_state.last_audio = digest
            if len(voice_bytes) < 2000:
                st.session_state.notice = (
                    "The recording was empty. Please tap the microphone, speak, "
                    "then tap stop - or type your question below."
                )
            else:
                with st.spinner(ui("listening")):
                    heard, heard_error = transcribe_audio(voice_bytes)
                if heard_error:
                    st.session_state.notice = heard_error
                else:
                    submit_question(heard, display=f"🎤 {heard}")
            st.session_state.voice_counter += 1
            st.rerun()

    if start > 0:
        with st.expander(ui("earlier")):
            for i in range(start):
                m = messages[i]
                if m["kind"] == "image":
                    st.image(m["content"], width=90)
                elif m["role"] == "user":
                    st.markdown(qchip_html(m["content"]), unsafe_allow_html=True)
                else:
                    st.markdown(
                        answer_card_html(
                            m["content"],
                            ui("explanation"),
                            ui("disclaimer"),
                            thumb_b64=find_thumb(messages, i),
                            compact=True,
                        ),
                        unsafe_allow_html=True,
                    )
                    if m.get("speakable"):
                        render_audio_controls(m, i, False)

    user_input = st.chat_input(
        ui("placeholder"),
        accept_file=True,
        file_type=["jpg", "jpeg", "png"],
    )
    if user_input:
        photo = user_input.files[0] if user_input.files else None
        text = user_input.text
        photo_bytes = photo.getvalue() if photo is not None else None
        if photo is not None and not looks_like_image(photo_bytes):
            st.session_state.notice = (
                "That file could not be opened as a photo. Please take a new, clear photo and try again."
            )
        else:
            submit_question(
                text or DEFAULT_PHOTO_QUESTION,
                display=text or None,
                photo_bytes=photo_bytes,
                mime=photo_mime(photo) if photo is not None else None,
            )
        st.rerun()


# ---------------------------------------------------------------------------
# Step 1: onboarding (same fields and behaviour as before, new look)
# ---------------------------------------------------------------------------
if "onboarded" not in st.session_state:
    inject_css()
    st.markdown(hero_html("", "", ui("hero_tag")), unsafe_allow_html=True)
    with st.form("onboarding_form"):
        name = st.text_input("Your name")
        whatsapp_number = st.text_input(
            "WhatsApp number (with country code)",
            placeholder="+91XXXXXXXXXX",
            help="WhatsApp opens a chat with this number with your summary ready to send. Use your own number to send it to yourself.",
        )
        submitted = st.form_submit_button("Let's go 🚀", type="primary", use_container_width=True)
    if submitted:
        if not name.strip() or not whatsapp_number.strip():
            st.warning("Please fill in both your name and WhatsApp number.")
        else:
            st.session_state.name = name.strip()
            st.session_state.whatsapp_number = whatsapp_number.strip()
            # Today's date is injected so the AI can judge expiry correctly.
            system_prompt = SYSTEM_PROMPT.format(today=date.today().strftime("%d %B %Y"))
            st.session_state.chat = gemini_client.chats.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.1,
                    max_output_tokens=700,
                ),
            )
            st.session_state.messages = []
            st.session_state.onboarded = True
            st.rerun()
    st.stop()

# State used by the screens and voice features
for _key, _default in {
    "view": "scan",           # "scan" (photo screen) or "result" (answer screen)
    "photo_sent": False,      # a medicine photo has been analysed
    "asked": False,           # a question was asked about the current medicine
    "analyzed_file": None,    # id of the uploaded photo that was analysed
    "audio_open": set(),      # older messages whose audio player was opened
    "scroll_top": False,      # jump to the top after a screen change
    "uploader_n": 0,          # changing the photo-box key empties it
    "voice_counter": 0,       # changing the mic widget key clears the old recording
    "last_audio": None,       # hash of the last recording handled
}.items():
    st.session_state.setdefault(_key, _default)

# ---------------------------------------------------------------------------
# Step 2: main interface
# ---------------------------------------------------------------------------
inject_css()
st.markdown(
    hero_html(st.session_state.name, ui("greet"), ui("hero_tag")),
    unsafe_allow_html=True,
)
tracker_slot = st.empty()  # filled in once we know how far along the user is

notice = st.session_state.pop("notice", None)
if notice:
    st.error(notice)
    st.toast(notice, icon="⚠️")

if st.session_state.pop("scroll_top", False):
    scroll_to_top()

if st.session_state.view == "result" and st.session_state.photo_sent:
    render_result_view(tracker_slot)
else:
    render_scan_view(tracker_slot)
