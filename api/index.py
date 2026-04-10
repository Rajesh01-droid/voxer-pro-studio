from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import edge_tts
import uuid
import os
import asyncio
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

AUDIO_DIR = "/tmp"

# Ultra-High Quality Neural Models (ElevenLabs Level)
# hi-IN-Madhuram aur Swara Roman Urdu ko behtareen samajhte hain
VOICE_MODELS = {
    "English": {"m": "en-US-AndrewNeural", "f": "en-US-AvaNeural"},
    "Hindi": {"m": "hi-IN-MadhuramNeural", "f": "hi-IN-SwaraNeural"}
}

class VoiceRequest(BaseModel):
    text: str
    voice_group: str
    gender: str

@app.post("/api/generate")
async def generate_voice(request: VoiceRequest):
    try:
        if not request.text.strip(): return {"error": "Script is empty"}
        
        # Smart Language & Model Selection
        lang = "Hindi" if request.voice_group == "Hindi" else "English"
        selected_voice = VOICE_MODELS[lang][request.gender]
        
        base_id = uuid.uuid4().hex[:6]
        filename = f"{request.gender}_{base_id}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        
        # Engine Settings for Natural Human Flow
        # Rate: +0% (Perfect for Roman Urdu), Pitch: -2Hz (Deep Studio Feel)
        communicate = edge_tts.Communicate(request.text, selected_voice, rate="+0%", pitch="-1Hz")
        await communicate.save(filepath)
        
        return {
            "status": "success",
            "url": f"/api/audio/{filename}",
            "voice_type": f"{lang} {request.gender.upper()}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio/{file_name}")
async def get_audio(file_name: str):
    file_path = os.path.join(AUDIO_DIR, file_name)
    return FileResponse(file_path) if os.path.exists(file_path) else HTTPException(404)
