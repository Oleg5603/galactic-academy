import tempfile
import os
import threading
import ctypes
import asyncio

# Edge TTS — разные голоса для каждого персонажа
EDGE_SETTINGS = {
    # Йода: медленно, чуть выше — старческий мудрый голос
    "yoda":  {"voice": "ru-RU-DmitryNeural", "rate": "-40%", "pitch": "+8Hz"},
    # Вейдер: медленно, очень низко — тёмный угрожающий
    "vader": {"voice": "ru-RU-DmitryNeural", "rate": "-25%", "pitch": "-30Hz"},
    # R2D2: очень быстро, выше — взволнованный дроид
    "r2d2":  {"voice": "ru-RU-DmitryNeural", "rate": "+50%", "pitch": "+25Hz"},
    # C3PO: чёткий, формальный, чуть роботизированный
    "c3po":  {"voice": "ru-RU-DmitryNeural", "rate": "+8%",  "pitch": "+15Hz"},
    # Оби-Ван: спокойный, тёплый наставник — естественный голос
    "obi":   {"voice": "ru-RU-DmitryNeural", "rate": "-10%", "pitch": "-5Hz"},
}

# pyttsx3 — резерв если нет интернета
SAPI_SETTINGS = {
    "yoda":  {"rate": 110},
    "vader": {"rate": 120},
    "r2d2":  {"rate": 210},
    "c3po":  {"rate": 160},
    "obi":   {"rate": 140},
}

_MCI_ALIAS = "ga_voice"
_mci = ctypes.windll.winmm.mciSendStringW


def stop():
    """Остановить воспроизведение."""
    _mci(f'stop {_MCI_ALIAS}', None, 0, None)
    _mci(f'close {_MCI_ALIAS}', None, 0, None)


def speak(text: str, character: str = "yoda") -> str:
    """Edge TTS (онлайн, качественный) → pyttsx3 (оффлайн, Irina)."""
    try:
        return _speak_edge(text, character)
    except Exception:
        return _speak_sapi(text, character)


def _speak_edge(text: str, character: str) -> str:
    import edge_tts
    cfg = EDGE_SETTINGS.get(character, EDGE_SETTINGS["obi"])
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tmp.close()

    async def _gen():
        comm = edge_tts.Communicate(
            text=text[:400], voice=cfg["voice"],
            rate=cfg["rate"], pitch=cfg["pitch"],
        )
        await comm.save(tmp.name)

    asyncio.run(_gen())
    if os.path.getsize(tmp.name) < 1000:
        raise RuntimeError("Edge TTS вернул пустой файл")
    return tmp.name


def _speak_sapi(text: str, character: str) -> str:
    import pyttsx3
    cfg = SAPI_SETTINGS.get(character, SAPI_SETTINGS["obi"])
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    ru = next((v for v in voices if 'ru' in v.id.lower() or 'russian' in v.name.lower()), None)
    if ru:
        engine.setProperty('voice', ru.id)
    engine.setProperty('rate', cfg["rate"])
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.close()
    engine.save_to_file(text[:400], tmp.name)
    engine.runAndWait()
    return tmp.name


def play(path: str):
    """Воспроизвести файл через Windows MCI."""
    def _play():
        stop()
        _mci(f'open "{path}" alias {_MCI_ALIAS}', None, 0, None)
        _mci(f'play {_MCI_ALIAS} wait', None, 0, None)
        _mci(f'close {_MCI_ALIAS}', None, 0, None)
    threading.Thread(target=_play, daemon=True).start()
