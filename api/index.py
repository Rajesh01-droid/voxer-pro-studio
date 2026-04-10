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

# Ultra-Clear Desi Models
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
        if not request.text.strip(): return {"error": "Empty"}
        
        lang = "Hindi" if "Hindi" in request.voice_group else "English"
        selected_voice = VOICE_MODELS[lang][request.gender]
        
        # PRONUNCIATION TUNING:
        # Roman Urdu ke liye rate thora slow (-8%) aur volume boost zaroori hai
        rate = "-8%" if lang == "Hindi" else "+0%"
        # Male voice ke liye thori base (-3Hz)
        pitch = "-3Hz" if request.gender == "m" and lang == "Hindi" else "+0Hz"
        
        base_id = uuid.uuid4().hex[:10]
        filename = f"{base_id}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        
        communicate = edge_tts.Communicate(request.text, selected_voice, rate=rate, pitch=pitch)
        await communicate.save(filepath)
        
        return {"status": "success", "url": f"/api/audio/{filename}?v={base_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio/{file_name}")
async def get_audio(file_name: str):
    file_path = os.path.join(AUDIO_DIR, file_name)
    return FileResponse(file_path) if os.path.exists(file_path) else HTTPException(404)
