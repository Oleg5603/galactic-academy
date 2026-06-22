import os
import tempfile
import subprocess
from gtts import gTTS

VOICE_SETTINGS = {
    "yoda":  {"lang": "ru", "slow": True},
    "vader": {"lang": "ru", "slow": False},
    "r2d2":  {"lang": "ru", "slow": False},
    "c3po":  {"lang": "ru", "slow": False},
    "obi":   {"lang": "ru", "slow": False},
}


def speak(text: str, character: str = "yoda") -> str:
    """Генерирует MP3 и возвращает путь к файлу."""
    settings = VOICE_SETTINGS.get(character, VOICE_SETTINGS["yoda"])
    tts = gTTS(text=text[:500], lang=settings["lang"], slow=settings["slow"])
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(tmp.name)
    return tmp.name


def play(path: str):
    """Воспроизводит MP3 через Windows Media Player."""
    subprocess.Popen(
        ["powershell", "-c", f'(New-Object Media.SoundPlayer).PlaySync()'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    os.startfile(path)
