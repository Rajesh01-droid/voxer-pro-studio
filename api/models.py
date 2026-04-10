import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import edge_tts
import uuid
import os
import random
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUDIO_DIR = "generated_audio"
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

class VoiceRequest(BaseModel):
    text: str
    voice: str

# Roman Urdu aur Hindi mix ke liye best Energetic Voices
VOICE_MAPPING = {
    "Adam (Male)": "en-US-SteffanNeural",      # Deep, Clear & Fast
    "Bella (Female)": "en-US-AvaNeural",        # Best for Roman Urdu/English mix
    "Urdu (Pakistan)": "ur-PK-AsadNeural",
    "Hindi (India)": "hi-IN-MadhurNeural",
    "Robo 2.0": "en-US-BrianNeural"
}

@app.get("/live-stats")
async def get_stats():
    return {
        "active_users": random.randint(500, 800),
        "total_generated": random.randint(12000, 15000),
        "server_load": f"{random.randint(5, 15)}%" # Optimized Load
    }

@app.post("/generate")
async def generate_voice(request: VoiceRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Script is empty!")

    try:
        filename = f"voxer_{uuid.uuid4().hex[:6]}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        
        selected_voice = VOICE_MAPPING.get(request.voice, "en-US-AvaNeural")

        # Voice settings for clarity and speed
        # Rate +10% fast taake bore na kare user ko
        communicate = edge_tts.Communicate(request.text, selected_voice, rate="+10%")
        await communicate.save(filepath)

        return {
            "status": "success",
            "audio_url": f"/audio/{filename}",
            "file_size": f"{round(os.path.getsize(filepath)/1024, 1)} KB"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")
app.mount("/", StaticFiles(directory=".", html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5500)