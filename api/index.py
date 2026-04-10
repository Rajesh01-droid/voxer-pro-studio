from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import edge_tts
import uuid
import os
import asyncio
from pydantic import BaseModel

app = FastAPI()

# Enable CORS for all requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

AUDIO_DIR = "/tmp"

# High-End Neural Models for Studio Quality
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
        if not request.text.strip():
            return {"error": "Script is empty"}
        
        # Explicit Language Selection
        lang = "Hindi" if "Hindi" in request.voice_group else "English"
        gender = "m" if request.gender == "m" else "f"
        
        selected_voice = VOICE_MODELS[lang][gender]
        
        # Audio Tuning for Crystal Clarity
        # Male voice ko heavy aur clear karne ke liye -2Hz pitch aur slow rate use kiya hai
        rate = "-4%" if gender == "m" else "+0%"
        pitch = "-2Hz" if gender == "m" else "+0Hz"
        
        base_id = uuid.uuid4().hex[:10]
        filename = f"{base_id}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        
        # Generate Audio
        communicate = edge_tts.Communicate(request.text, selected_voice, rate=rate, pitch=pitch)
        await communicate.save(filepath)
        
        return {
            "status": "success", 
            "url": f"/api/audio/{filename}?v={base_id}",
            "meta": f"{lang} {gender.upper()}"
        }
    except Exception as e:
        print(f"Backend Error: {e}")
        raise HTTPException(status_code=500, detail="Neural Engine Failure")

@app.get("/api/audio/{file_name}")
async def get_audio(file_name: str):
    file_path = os.path.join(AUDIO_DIR, file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    return {"error": "File not found"}
