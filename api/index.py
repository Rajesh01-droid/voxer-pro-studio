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

# Ultra-High Quality Neural Voices
VOICES = {
    "English": {"male": "en-US-AndrewNeural", "female": "en-US-EmmaNeural"},
    "Hindi": {"male": "hi-IN-MadhuramNeural", "female": "hi-IN-SwaraNeural"}
}

class VoiceRequest(BaseModel):
    text: str
    voice_group: str

@app.post("/api/generate")
async def generate_voice(request: VoiceRequest):
    try:
        if not request.text.strip():
            return {"error": "Text empty"}

        group = VOICES.get(request.voice_group, VOICES["Hindi"])
        base_id = uuid.uuid4().hex[:8]
        
        # 3 Professional Styles
        styles = [
            {"name": "Professional HD", "rate": "+0%", "pitch": "+0Hz", "id": "prof"},
            {"name": "Fast & Energetic", "rate": "+25%", "pitch": "+1Hz", "id": "fast"},
            {"name": "Slow & Narrative", "rate": "-15%", "pitch": "-2Hz", "id": "slow"}
        ]
        
        tasks = []
        male_samples = []
        female_samples = []

        for s in styles:
            # Male Generation
            m_file = f"m_{s['id']}_{base_id}.mp3"
            m_path = os.path.join(AUDIO_DIR, m_file)
            tasks.append(edge_tts.Communicate(request.text, group["male"], rate=s['rate'], pitch=s['pitch']).save(m_path))
            male_samples.append({"style": s['name'], "url": f"/api/audio/{m_file}"})

            # Female Generation
            f_file = f"f_{s['id']}_{base_id}.mp3"
            f_path = os.path.join(AUDIO_DIR, f_file)
            tasks.append(edge_tts.Communicate(request.text, group["female"], rate=s['rate'], pitch=s['pitch']).save(f_path))
            female_samples.append({"style": s['name'], "url": f"/api/audio/{f_file}"})

        await asyncio.gather(*tasks)
        
        return {
            "status": "success",
            "male_samples": male_samples,
            "female_samples": female_samples
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio/{file_name}")
async def get_audio(file_name: str):
    file_path = os.path.join(AUDIO_DIR, file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    raise HTTPException(status_code=404)
