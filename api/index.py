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

# Vercel's only writable directory
AUDIO_DIR = "/tmp"

VOICES = {
    "English": {"male": "en-US-AndrewNeural", "female": "en-US-EmmaNeural"},
    "Hindi": {"male": "hi-IN-MadhuramNeural", "female": "hi-IN-SwaraNeural"}
}

class VoiceRequest(BaseModel):
    text: str
    voice_group: str

@app.get("/api/live-stats")
async def stats():
    return {"active_users": "1,240", "total_generated": "85K+", "server_load": "2%"}

@app.post("/api/generate")
async def generate_voice(request: VoiceRequest):
    try:
        if not request.text.strip():
            return {"error": "Text is empty"}

        group = VOICES.get(request.voice_group, VOICES["Hindi"])
        base_id = uuid.uuid4().hex[:8]
        
        # We will generate only 1 sample first to test speed
        filename = f"m_{base_id}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        
        communicate = edge_tts.Communicate(request.text, group["male"])
        await communicate.save(filepath)
        
        # Return proper structure for your frontend
        sample_url = f"/api/audio/{filename}"
        return {
            "status": "success",
            "male_samples": [{"style": "Crystal Clear HD", "url": sample_url}],
            "female_samples": [{"style": "Natural Soft", "url": sample_url}]
        }
    except Exception as e:
        # This will show in Vercel Logs
        print(f"CRITICAL ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio/{file_name}")
async def get_audio(file_name: str):
    file_path = os.path.join(AUDIO_DIR, file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    return {"error": "File not found"}
