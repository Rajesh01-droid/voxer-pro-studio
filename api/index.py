from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import edge_tts
import uuid
import os
import asyncio
from pydantic import BaseModel

app = FastAPI()

# Sab ko allow karo taake connection error na aaye
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

AUDIO_DIR = "/tmp"

# High-Quality Neural Voices for Roman Urdu/Hindi/English
VOICE_MODELS = {
    "English": {"m": "en-US-AndrewNeural", "f": "en-US-AvaNeural"},
    "Hindi": {"m": "hi-IN-MadhuramNeural", "f": "hi-IN-SwaraNeural"}
}

class VoiceRequest(BaseModel):
    text: str
    voice_group: str # 'English' or 'Hindi'
    gender: str      # 'm' or 'f'

@app.post("/api/generate")
async def generate_voice(request: VoiceRequest):
    try:
        if not request.text.strip():
            return {"error": "Text empty"}
        
        # Force selection based on front-end signal
        lang_group = VOICE_MODELS.get(request.voice_group, VOICE_MODELS["English"])
        voice_id = lang_group.get(request.gender, lang_group["m"])
        
        unique_id = uuid.uuid4().hex[:10]
        filename = f"{unique_id}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        
        # Crystal Clear Neural Generation
        communicate = edge_tts.Communicate(request.text, voice_id, rate="+0%", pitch="-1Hz")
        await communicate.save(filepath)
        
        return {"status": "success", "url": f"/api/audio/{filename}"}
    
    except Exception as e:
        print(f"System Error: {e}")
        raise HTTPException(status_code=500, detail="Generation Failed")

@app.get("/api/audio/{file_name}")
async def get_audio(file_name: str):
    file_path = os.path.join(AUDIO_DIR, file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    return {"error": "File Not Found"}
