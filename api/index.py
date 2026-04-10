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

# High-End Neural Models
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
            return {"error": "Text is empty"}
        
        # Explicitly choosing voice based on request to avoid state issues
        target_group = VOICE_MODELS.get(request.voice_group, VOICE_MODELS["English"])
        selected_voice = target_group.get(request.gender, target_group["m"])
        
        base_id = uuid.uuid4().hex[:8]
        filename = f"{base_id}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        
        # Studio Quality settings
        communicate = edge_tts.Communicate(request.text, selected_voice, rate="+0%", pitch="-1Hz")
        await communicate.save(filepath)
        
        return {
            "status": "success",
            "url": f"/api/audio/{filename}?v={base_id}" # Versioning to bypass browser cache
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/audio/{file_name}")
async def get_audio(file_name: str):
    file_path = os.path.join(AUDIO_DIR, file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    return {"error": "File not found"}
