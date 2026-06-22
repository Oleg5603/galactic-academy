import asyncio
import tempfile
import os
import httpx
import edge_tts

# ElevenLabs встроенные голоса
ELEVEN_VOICE_IDS = {
    "yoda":  "Zlb1dXrM653N07WRdFW3",  # Joseph — глубокий британский, мудрый
    "vader": "pNInz6obpgDQGcFmaJgB",  # Adam — тёмный, доминантный
    "r2d2":  "yoZ06aMxZJJ28mfd3POQ",  # Sam — хриплый, энергичный
    "c3po":  "onwK4e9ZLuTAKqWW03F9",  # Daniel — британский, формальный
    "obi":   "29vD33N1lfvaU8JoGGsw",  # Drew — тёплый, мудрый наставник
}

# Edge TTS — резервный вариант (без лимитов, мужской голос Дмитрий)
EDGE_SETTINGS = {
    "yoda":  {"voice": "ru-RU-DmitryNeural", "rate": "-25%", "pitch": "-8Hz"},
    "vader": {"voice": "ru-RU-DmitryNeural", "rate": "-20%", "pitch": "-25Hz"},
    "r2d2":  {"voice": "ru-RU-DmitryNeural", "rate": "+35%", "pitch": "+20Hz"},
    "c3po":  {"voice": "ru-RU-DmitryNeural", "rate": "+5%",  "pitch": "+8Hz"},
    "obi":   {"voice": "ru-RU-DmitryNeural", "rate": "-5%",  "pitch": "+0Hz"},
}

ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")


def speak(text: str, character: str = "yoda") -> str:
    """Генерирует MP3: ElevenLabs если есть ключ+ID, иначе Edge TTS."""
    voice_id = ELEVEN_VOICE_IDS.get(character, "")
    if ELEVEN_API_KEY and voice_id:
        return _speak_eleven(text, voice_id)
    return _speak_edge(text, character)


def _speak_eleven(text: str, voice_id: str) -> str:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    r = httpx.post(
        url,
        headers={"xi-api-key": ELEVEN_API_KEY, "Content-Type": "application/json"},
        json={"text": text[:400], "model_id": "eleven_multilingual_v2",
              "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}},
        timeout=20,
    )
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tmp.write(r.content)
    tmp.close()
    return tmp.name


def _speak_edge(text: str, character: str) -> str:
    cfg = EDGE_SETTINGS.get(character, EDGE_SETTINGS["obi"])
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tmp.close()

    async def _gen():
        comm = edge_tts.Communicate(
            text=text[:400],
            voice=cfg["voice"],
            rate=cfg["rate"],
            pitch=cfg["pitch"],
        )
        await comm.save(tmp.name)

    asyncio.run(_gen())
    return tmp.name


def play(path: str):
    import subprocess
    subprocess.Popen(
        ['powershell', '-c',
         f'$mp = New-Object System.Windows.Media.MediaPlayer;'
         f'$mp.Open([System.Uri]::new("{path}"));'
         f'$mp.Play();'
         f'Start-Sleep -Seconds 10;'
         f'$mp.Stop()'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
