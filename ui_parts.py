"""Look & feel for MediScan: CSS, header, progress tracker, answer card, audio player.

Everything here returns plain HTML/CSS strings and imports nothing from
Streamlit, so app.py stays about behaviour and this file stays about looks.

Design idea: a medicine BLISTER PACK.
  * the 4-step progress tracker is a foil strip with one "pill cup" per step
  * the header carries a two-tone capsule
  * the explanation is a pharmacy LABEL with punched holes along its edge
  * buttons are pill-shaped and press down like real buttons
Palette: ink #0F2A3D, teal #00957F, saffron #FFB02E, rose #E5484D, foil #EAF0F3.
Fonts: Baloo (friendly headings) + Atkinson Hyperlegible (made for low vision)
+ Noto Sans for each Indian script. If the fonts cannot load, system fonts are used.
"""

import html
import re

esc = html.escape

_EMOJI_RE = re.compile("[\U0001F000-\U0001FFFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]")


def strip_icon(text):
    """Remove emoji from a label (used where the design draws its own icon)."""
    return " ".join(_EMOJI_RE.sub("", text).split())


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Baloo+2:wght@500;700;800&family=Baloo+Tammudu+2:wght@500;700;800&family=Baloo+Thambi+2:wght@500;700;800&family=Baloo+Tamma+2:wght@500;700;800&family=Baloo+Chettan+2:wght@500;700;800&family=Noto+Sans+Devanagari:wght@400;700&family=Noto+Sans+Telugu:wght@400;700&family=Noto+Sans+Tamil:wght@400;700&family=Noto+Sans+Kannada:wght@400;700&family=Noto+Sans+Malayalam:wght@400;700&display=swap');
:root{
  --ink:#0F2A3D; --ink2:#3B5A6E; --teal:#00957F; --teal-d:#006F5F; --saffron:#FFB02E;
  --rose:#E5484D; --foil:#EAF0F3; --line:#C9D6DD; --card:#FFFFFF; color-scheme:light;
  --body:'Atkinson Hyperlegible','Noto Sans Devanagari','Noto Sans Telugu','Noto Sans Tamil','Noto Sans Kannada','Noto Sans Malayalam','Nirmala UI','Segoe UI',system-ui,sans-serif;
  --head:'Baloo 2','Baloo Tammudu 2','Baloo Thambi 2','Baloo Tamma 2','Baloo Chettan 2','Noto Sans Devanagari','Noto Sans Telugu','Noto Sans Tamil','Noto Sans Kannada','Noto Sans Malayalam','Nirmala UI','Segoe UI',sans-serif;
}
.stApp{background-color:var(--foil);background-image:radial-gradient(rgba(15,42,61,.07) 1.5px,transparent 1.6px);background-size:24px 24px;color:var(--ink);font-family:var(--body)}
.stApp p,.stApp li,.stApp label,.stApp input,.stApp textarea,.stApp button,.stApp summary{font-family:var(--body)}
.stApp h1,.stApp h2,.stApp h3{font-family:var(--head) !important;color:var(--ink)}
.block-container{max-width:780px !important;padding-top:1rem !important;padding-bottom:8rem !important}
header[data-testid="stHeader"]{background:transparent}
[data-testid="stToolbar"],[data-testid="stDecoration"],footer,#MainMenu{display:none !important}
div[data-testid="stElementContainer"]:has(iframe[height="0"]),.element-container:has(iframe[height="0"]){display:none}

/* ---------- header ---------- */
.hero{display:flex;align-items:center;gap:1rem;flex-wrap:wrap;background:var(--ink);color:#fff;border-radius:30px;padding:1rem 1.3rem;margin-bottom:.6rem;
  background-image:radial-gradient(rgba(255,255,255,.11) 6px,transparent 7px);background-size:26px 26px;background-position:right top;overflow:hidden}
.caps{flex:none;width:66px;height:28px;border-radius:999px;position:relative;margin:14px 10px 14px 4px;transform:rotate(-35deg);
  background:linear-gradient(90deg,var(--saffron) 50%,#fff 50%);box-shadow:inset 0 -5px 0 rgba(0,0,0,.14),0 8px 16px rgba(0,0,0,.35);animation:capsIn .8s cubic-bezier(.2,.9,.3,1.2) both}
.caps::after{content:"";position:absolute;left:8px;top:5px;width:24px;height:5px;border-radius:5px;background:rgba(255,255,255,.6)}
@keyframes capsIn{from{transform:rotate(-250deg) scale(.3);opacity:0}to{transform:rotate(-35deg) scale(1);opacity:1}}
.hero-txt{flex:1 1 220px;min-width:0}
.hero-name{font-family:var(--head);font-weight:800;font-size:2.1rem;line-height:1.05;letter-spacing:.01em}
.hero-tag{font-size:1.05rem;opacity:.85;margin-top:.15rem}
.hero-hi{flex:none;background:rgba(255,255,255,.14);border-radius:999px;padding:.35rem 1rem;font-weight:700;font-size:1.05rem}

/* ---------- blister-strip tracker ---------- */
.blister{position:relative;display:flex;background:#fff;border-radius:999px;padding:.75rem .6rem .6rem;margin:.2rem 0 1rem;box-shadow:inset 0 0 0 2px var(--line)}
.blister::before{content:"";position:absolute;left:13%;right:13%;top:2.2rem;border-top:3px dashed var(--line)}
.bl{flex:1;text-align:center;position:relative;z-index:1;min-width:0}
.bl .cup{width:3.1rem;height:3.1rem;margin:0 auto;border-radius:50%;display:grid;place-items:center;font-size:1.45rem;background:var(--foil);box-shadow:inset 0 4px 7px rgba(15,42,61,.28),0 1px 0 #fff}
.bl .cap{font-size:.95rem;font-weight:700;margin-top:.3rem;color:var(--ink2);overflow-wrap:anywhere;padding:0 .1rem}
.bl.done .cup{background:var(--teal);color:#fff;font-weight:800;box-shadow:inset 0 -5px 0 rgba(0,0,0,.2),0 4px 9px rgba(0,149,127,.4)}
.bl.done .cap{color:var(--teal-d)}
.bl.active .cup{background:var(--saffron);box-shadow:inset 0 -5px 0 rgba(0,0,0,.15),0 0 0 5px rgba(255,176,46,.38);animation:pulse 1.8s ease-in-out infinite}
.bl.active .cap{color:var(--ink)}
@keyframes pulse{0%,100%{box-shadow:inset 0 -5px 0 rgba(0,0,0,.15),0 0 0 4px rgba(255,176,46,.45)}50%{box-shadow:inset 0 -5px 0 rgba(0,0,0,.15),0 0 0 11px rgba(255,176,46,0)}}

/* ---------- cards & headings ---------- */
.st-key-scan_card,.st-key-go_card,.st-key-ask_card,.st-key-share_card{background:var(--card);border-radius:26px;padding:1.05rem 1.2rem 1.25rem;margin-bottom:1rem;
  border:2px solid rgba(15,42,61,.08);box-shadow:0 1px 0 rgba(15,42,61,.05),0 16px 28px -22px rgba(15,42,61,.5)}
.sec{font-family:var(--head);font-weight:800;font-size:1.5rem;line-height:1.25;color:var(--ink);margin:.1rem 0 .5rem}
.hint{font-size:1.1rem;color:var(--ink2);margin:-.2rem 0 .7rem}

/* ---------- buttons: pill shaped, they press down ---------- */
.stButton>button{min-height:3.7rem;border-radius:999px;border:2px solid var(--ink);background:#fff;color:var(--ink);font-weight:700;
  box-shadow:0 4px 0 var(--ink);transition:transform .08s ease,box-shadow .08s ease,filter .15s}
.stButton>button p{font-size:1.22rem;font-weight:700}
.stButton>button:hover{filter:brightness(.97);transform:translateY(-1px)}
.stButton>button:active{transform:translateY(4px);box-shadow:0 0 0 var(--ink)}
.stButton>button:focus-visible{outline:4px solid var(--saffron);outline-offset:3px}
.stButton>button:disabled{opacity:.45;box-shadow:none}
.stButton>button[kind="primary"],.stButton>button[data-testid="stBaseButton-primary"]{background:var(--teal);border-color:var(--teal-d);color:#fff;box-shadow:0 5px 0 var(--teal-d)}
.stButton>button[kind="primary"]:active,.stButton>button[data-testid="stBaseButton-primary"]:active{box-shadow:0 0 0 var(--teal-d)}
.stButton>button[kind="primary"] p,.stButton>button[data-testid="stBaseButton-primary"] p{color:#fff}
.st-key-identify button{min-height:4.8rem !important}
.st-key-identify button p{font-size:1.6rem !important;font-family:var(--head)}
.st-key-identify button:not(:disabled){animation:glow 2.2s ease-in-out infinite}
@keyframes glow{0%,100%{box-shadow:0 5px 0 var(--teal-d),0 0 0 0 rgba(0,149,127,.5)}60%{box-shadow:0 5px 0 var(--teal-d),0 0 0 14px rgba(0,149,127,0)}}
.st-key-quick .stButton>button{min-height:3.4rem;justify-content:flex-start;text-align:left;padding:.35rem 1.1rem;box-shadow:0 3px 0 rgba(15,42,61,.28);border-color:rgba(15,42,61,.4)}
.st-key-quick .stButton>button p{font-size:1.12rem}
.st-key-quick .stButton>button:hover:not(:disabled){background:var(--saffron);border-color:var(--ink)}
a[data-testid^="stBaseLinkButton"]{min-height:4rem;border-radius:999px !important;background:#25D366 !important;border:2px solid #128C4A !important;box-shadow:0 5px 0 #128C4A;color:#05361B !important;font-weight:800}
a[data-testid^="stBaseLinkButton"] p{font-size:1.3rem;color:#05361B !important;font-weight:800}

/* ---------- photo box ---------- */
[data-testid="stFileUploaderDropzone"]{border:3px dashed var(--teal) !important;border-radius:22px !important;background:rgba(0,149,127,.07) !important;
  min-height:8.5rem;display:flex !important;flex-direction:column;align-items:center;justify-content:center;gap:.5rem;padding:1.1rem}
[data-testid="stFileUploaderDropzoneInstructions"]{display:none !important}
[data-testid="stFileUploaderDropzone"] button{min-height:4rem;padding:0 1.8rem !important;border-radius:999px !important;background:var(--teal) !important;border:0 !important;box-shadow:0 4px 0 var(--teal-d)}
[data-testid="stFileUploaderDropzone"] button>*{display:none !important}
[data-testid="stFileUploaderDropzone"] button::after{content:__BROWSE__;font-size:1.35rem;font-weight:800;color:#fff;font-family:var(--body)}
[data-testid="stImage"] img{border-radius:18px;border:3px solid #fff;box-shadow:0 8px 18px -10px rgba(15,42,61,.6)}

/* ---------- microphone, typing box, alerts, expanders ---------- */
/* ---------- voice-first microphone ---------- */
.voice-hub{display:flex;flex-direction:column;align-items:center;justify-content:center;
  background:#fff;border:3px solid var(--ink);border-radius:28px;padding:1rem 1rem .8rem;
  margin:.2rem 0 .8rem;box-shadow:0 7px 0 rgba(15,42,61,.12)}
.voice-orb{width:92px;height:92px;border-radius:50%;display:grid;place-items:center;
  background:var(--teal);color:#fff;font-size:2.8rem;border:7px solid #D7F3EE;
  box-shadow:0 0 0 5px rgba(0,149,127,.12),0 8px 18px rgba(0,111,95,.25);
  animation:micPulse 2.2s ease-in-out infinite}
.voice-title{font-family:var(--head);font-size:1.45rem;font-weight:800;color:var(--ink);margin-top:.65rem;text-align:center}
.voice-sub{font-size:1rem;color:var(--ink2);text-align:center;margin-top:.15rem}
@keyframes micPulse{0%,100%{transform:scale(1);box-shadow:0 0 0 5px rgba(0,149,127,.12),0 8px 18px rgba(0,111,95,.25)}
50%{transform:scale(1.04);box-shadow:0 0 0 12px rgba(0,149,127,0),0 10px 22px rgba(0,111,95,.25)}}
[data-testid="stAudioInput"]{border-radius:24px !important;border:3px solid var(--ink) !important;background:#fff !important;padding:.45rem .65rem !important;
  min-height:4.7rem;box-shadow:0 4px 0 rgba(15,42,61,.16)}
[data-testid="stAudioInput"] button{min-height:4rem !important;min-width:4rem !important;border-radius:50% !important;
  background:var(--teal) !important;color:#fff !important;border:0 !important;box-shadow:0 4px 0 var(--teal-d) !important}
[data-testid="stChatInput"]{border-radius:999px !important;border:3px solid var(--ink) !important;background:#fff}
[data-testid="stChatInput"] textarea{font-size:1.2rem !important}
[data-testid="stBottom"]>div{background:transparent !important}
[data-testid="stAlert"]{border-radius:18px;font-size:1.12rem}
[data-testid="stExpander"]{border:2px solid var(--line) !important;border-radius:20px !important;background:#fff}
[data-testid="stExpander"] summary p{font-size:1.2rem;font-weight:700}
[data-testid="stForm"]{background:#fff;border-radius:26px;border:2px solid rgba(15,42,61,.08);padding:1.2rem}
.stTextInput label p{font-size:1.15rem;font-weight:700}
.stTextInput input{font-size:1.2rem;min-height:3rem}

/* ---------- the pharmacy label that holds an explanation ---------- */
.mlabel{position:relative;background:#fff;border-radius:6px 30px 30px 6px;margin:.4rem 0 .6rem;padding:1.05rem 1.3rem 1rem 1.6rem;
  border-left:16px solid var(--teal);box-shadow:0 1px 0 rgba(15,42,61,.06),0 16px 28px -20px rgba(15,42,61,.55)}
.mlabel::before{content:"";position:absolute;left:-16px;top:10px;bottom:10px;width:16px;
  background:radial-gradient(circle at 8px 8px,var(--foil) 4.2px,transparent 4.8px) 0 0/16px 26px repeat-y}
.mhead{display:flex;align-items:center;justify-content:space-between;gap:.8rem;padding-bottom:.4rem}
.mtitle{font-family:var(--head);font-weight:800;font-size:1.35rem;color:var(--teal-d)}
.mthumb{width:74px;height:74px;object-fit:cover;border-radius:16px;border:3px solid var(--foil);flex:none}
.lrow{display:grid;grid-template-columns:minmax(7.5rem,30%) 1fr;gap:.1rem 1rem;padding:.6rem 0;border-top:2px dashed var(--line)}
.lrow.plain{grid-template-columns:1fr}
.lk{font-weight:800;font-size:1.12rem;color:var(--teal-d);line-height:1.5}
.lv{font-size:1.4rem;line-height:1.6;overflow-wrap:anywhere}
.mwarn{margin-top:.5rem;padding:.55rem .9rem;border-radius:14px;background:rgba(255,176,46,.22);font-size:1rem;line-height:1.45;color:#5A3B00}
.mlabel.compact .lv{font-size:1.18rem}.mlabel.compact .mthumb{width:52px;height:52px}.mlabel.compact .mwarn{display:none}
.qchip{margin:.5rem 0 .3rem auto;width:fit-content;max-width:92%;background:var(--ink);color:#fff;border-radius:24px 24px 6px 24px;padding:.6rem 1.1rem;font-size:1.2rem;font-weight:700;line-height:1.45;overflow-wrap:anywhere}
@media (max-width:560px){
  .lrow{grid-template-columns:1fr}.lv{font-size:1.32rem}.hero-name{font-size:1.8rem}.hero-hi{display:none}
  .bl .cup{width:2.6rem;height:2.6rem;font-size:1.2rem}.blister::before{top:2rem}.bl .cap{font-size:.85rem}
}
@media (prefers-reduced-motion:reduce){.caps,.bl.active .cup,.st-key-identify button:not(:disabled){animation:none}}
</style>
"""


def css(browse_label):
    """The page style. `browse_label` replaces the English 'Browse files' text."""
    safe = browse_label.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    return _CSS.replace("__BROWSE__", f'"{safe}"')


# ---------------------------------------------------------------------------
# Small HTML pieces (single-line strings: no blank lines, so Markdown leaves them alone)
# ---------------------------------------------------------------------------
def section_html(text):
    return f'<div class="sec">{esc(text)}</div>'


def hero_html(name, greet, tagline):
    hi = f'<div class="hero-hi">{esc(greet)}, {esc(name)}</div>' if name else ""
    return (
        '<div class="hero"><div class="caps"></div><div class="hero-txt">'
        '<div class="hero-name">MediScan</div>'
        f'<div class="hero-tag">{esc(tagline)}</div></div>{hi}</div>'
    )


def tracker_html(steps):
    """steps = [(icon, label, state)], state is 'done', 'active' or 'todo'."""
    cells = []
    for icon, label, state in steps:
        inner = "✓" if state == "done" else icon
        cells.append(
            f'<div class="bl {state}"><div class="cup">{inner}</div><div class="cap">{esc(label)}</div></div>'
        )
    return f'<div class="blister">{"".join(cells)}</div>'


def tracker_states(done_flags):
    """[True, True, False, False] -> ['done', 'done', 'active', 'todo']"""
    out, active_set = [], False
    for done in done_flags:
        if done:
            out.append("done")
        elif not active_set:
            out.append("active")
            active_set = True
        else:
            out.append("todo")
    return out


def qchip_html(text):
    return f'<div class="qchip">{esc(text)}</div>'


_LABEL = re.compile(r"^([^:：]{1,28}?)\s*[:：]\s*(\S.*)$")
_BULLET = re.compile(r"^\s*(?:[-*•●▪]+|\d{1,2}[.)])\s+")


def _rows(text):
    rows = []
    for raw in (text or "").splitlines():
        line = _BULLET.sub("", raw).strip()
        if not line:
            continue
        m = _LABEL.match(line)
        if m and not re.search(r"[\d.,;!?()]", m.group(1)):
            rows.append(
                f'<div class="lrow"><div class="lk">{esc(m.group(1))}</div>'
                f'<div class="lv">{esc(m.group(2))}</div></div>'
            )
        else:
            rows.append(f'<div class="lrow plain"><div class="lv">{esc(line)}</div></div>')
    return "".join(rows)


def answer_card_html(text, title, disclaimer, thumb_b64=None, question=None, compact=False):
    """The pharmacy-label card. 'Used for: ...' lines become two-column rows."""
    thumb = f'<img class="mthumb" alt="" src="data:image/jpeg;base64,{thumb_b64}">' if thumb_b64 else ""
    cls = "mlabel compact" if compact else "mlabel"
    return (
        (qchip_html(question) if question else "")
        + f'<div class="{cls}"><div class="mhead"><span class="mtitle">💊 {esc(strip_icon(title))}</span>{thumb}</div>'
        + _rows(text)
        + f'<div class="mwarn">{esc(disclaimer)}</div></div>'
    )
