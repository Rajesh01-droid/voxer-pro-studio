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

# ElevenLabs Equivalent High-End Models
VOICE_MODELS = {
    "English": {"m": "en-US-AndrewNeural", "f": "en-US-AvaNeural"},
    "Hindi": {"m": "hi-IN-MadhuramNeural", "f": "hi-IN-SwaraNeural"}
}

class VoiceRequest(BaseModel):
    text: str
    voice_group: str

@app.post("/api/generate")
async def generate_voice(request: VoiceRequest):
    try:
        if not request.text.strip(): return {"error": "Text is empty"}
        
        # Smart Selection Logic
        lang = "Hindi" if request.voice_group == "Hindi" else "English"
        group = VOICE_MODELS[lang]
        
        base_id = uuid.uuid4().hex[:6]
        
        # 3 Smart Levels: Professional, Deep, aur Soft (ElevenLabs Style)
        configs = [
            {"id": f"m_pro_{base_id}", "v": group["m"], "r": "+0%", "p": "+0Hz", "label": "Professional Studio"},
            {"id": f"f_pro_{base_id}", "v": group["f"], "r": "+0%", "p": "+0Hz", "label": "Crystal Female (HD)"},
            {"id": f"m_deep_{base_id}", "v": group["m"], "r": "-5%", "p": "-3Hz", "label": "Deep Narrative (BASS)"}
        ]
        
        tasks = []
        male_samples = []
        female_samples = []

        for c in configs:
            path = os.path.join(AUDIO_DIR, f"{c['id']}.mp3")
            # Creating the task
            tasks.append(edge_tts.Communicate(request.text, c["v"], rate=c["r"], pitch=c["p"]).save(path))
            
            sample_data = {"style": c["label"], "url": f"/api/audio/{c['id']}.mp3"}
            if c["id"].startswith("m_"): male_samples.append(sample_data)
            else: female_samples.append(sample_data)

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
    return FileResponse(file_path) if os.path.exists(file_path) else HTTPException(404)
