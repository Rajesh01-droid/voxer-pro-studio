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

# 100% Fixed Models for Roman Urdu/Hindi
# Madhuram is the king of Urdu Male voices
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
            return {"error": "Empty text"}
        
        # LOGIC FIX: Force Hindi if keywords are found or if selected
        v_group = request.voice_group
        # Agar text mein desi words hain toh force Hindi
        desi_keywords = ["hai", "kya", "thek", "kam", "zindagi", "salaam", "bhai"]
        if any(word in request.text.lower() for word in desi_keywords):
            v_group = "Hindi"

        group = VOICE_MODELS.get(v_group, VOICE_MODELS["Hindi"])
        # Explicitly choosing Male/Female
        selected_voice = group["m"] if request.gender == "m" else group["f"]
        
        base_id = uuid.uuid4().hex[:10]
        filename = f"{base_id}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        
        # Pitch optimized for deep male voice
        communicate = edge_tts.Communicate(request.text, selected_voice, rate="+0%", pitch="-2Hz")
        await communicate.save(filepath)
        
        return {"status": "success", "url": f"/api/audio/{filename}?v={base_id}"}
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Neural Engine Error")

@app.get("/api/audio/{file_name}")
async def get_audio(file_name: str):
    file_path = os.path.join(AUDIO_DIR, file_name)
    return FileResponse(file_path) if os.path.exists(file_path) else HTTPException(404)
