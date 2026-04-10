from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import edge_tts
import uuid
import os
import asyncio
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

AUDIO_DIR = "/tmp"

# 100% Best Neural Voices for Hindi/Urdu/English
VOICES = {
    "English": "en-US-AndrewNeural",
    "Hindi": "hi-IN-MadhuramNeural" # Ye sabse clear Hindi/Urdu voice hai
}

class VoiceRequest(BaseModel):
    text: str
    voice_group: str

@app.post("/api/generate")
async def generate_voice(request: VoiceRequest):
    try:
        if not request.text.strip():
            return {"error": "Text is empty"}

        # Voice selection
        selected_voice = VOICES.get(request.voice_group, VOICES["Hindi"])
        
        base_id = uuid.uuid4().hex[:8]
        filename = f"{base_id}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        
        # Crystal Clear Audio Settings
        # Rate +0% (Normal speed), Pitch +0Hz (Natural tone)
        communicate = edge_tts.Communicate(request.text, selected_voice, rate="+0%", pitch="+0Hz")
        await communicate.save(filepath)
        
        sample_url = f"/api/audio/{filename}"
        
        # Return samples in the format your frontend expects
        return {
            "status": "success",
            "male_samples": [{"style": "Crystal Clear HD", "url": sample_url}],
            "female_samples": [{"style": "Natural Neural", "url": sample_url}]
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio/{file_name}")
async def get_audio(file_name: str):
    file_path = os.path.join(AUDIO_DIR, file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="File not found")
