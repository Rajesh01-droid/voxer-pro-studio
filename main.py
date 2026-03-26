import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import time
import random
import os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class VoiceRequest(BaseModel):
    text: str
    voice: str

# Voice map
VOICE_MAP = {
    "Adam (Male)": "audio/male_adam.mp3",
    "Bella (Female)": "audio/female_bella.mp3",
    "Asad (Urdu)": "audio/urdu_asad.mp3",
    "Robo 2.0": "audio/robo2.mp3"
}

# --- API: Live Stats ---
@app.get("/live-stats")
async def get_stats():
    return {
        "active_users": random.randint(1100, 1400),
        "total_generated": random.randint(145000, 146000),
        "server_load": f"{random.randint(10, 30)}%"
    }

# --- API: Generate Voice ---
@app.post("/generate")
async def generate_voice(request: VoiceRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Script is empty!")

    voice_file = VOICE_MAP.get(request.voice)
    if not voice_file or not os.path.exists(voice_file):
        raise HTTPException(status_code=404, detail="Selected voice file not found!")

    # Simulate processing delay
    time.sleep(1)

    return {
        "status": "success",
        "duration": "00:42s",
        "file_size": f"{round(os.path.getsize(voice_file)/1024/1024,1)} MB",
        "audio_url": f"/{voice_file.replace(os.sep,'/')}"
    }

# --- Serve frontend ---
if os.path.exists("."):
    app.mount("/", StaticFiles(directory=".", html=True), name="frontend")

# --- Serve audio folder ---
if os.path.exists("audio"):
    app.mount("/audio", StaticFiles(directory="audio"), name="audio")

# --- Run server ---
if __name__ == "__main__":
    print("🚀 Voxer AI Server Starting at http://127.0.0.1:5500")
    uvicorn.run(app, host="127.0.0.1", port=5500, reload=True)