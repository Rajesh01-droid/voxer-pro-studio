import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import edge_tts
import uuid
import os
import asyncio
from pydantic import BaseModel

app = FastAPI()

# CORS settings taake frontend backend se baat kar sakay
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Vercel par sirf /tmp folder mein writing permission hoti hai
AUDIO_DIR = "/tmp"

# Voices Dictionary
VOICES = {
    "English": {"male": "en-US-AndrewNeural", "female": "en-US-EmmaNeural"},
    "Hindi": {"male": "hi-IN-MadhuramNeural", "female": "hi-IN-SwaraNeural"}
}

class VoiceRequest(BaseModel):
    text: str
    voice_group: str

def clean_text(text, lang):
    # Basic cleaning
    return text.strip()

def get_voice_style(text):
    # Default rate and pitch
    return "+0%", "+0Hz"

@app.post("/api/generate")
async def generate_voice(request: VoiceRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text required")
    
    group = VOICES.get(request.voice_group, VOICES["Hindi"])
    processed_text = clean_text(request.text, request.voice_group)
    rate_adj, pitch_adj = get_voice_style(processed_text)

    try:
        base_id = uuid.uuid4().hex[:8]
        styles = [
            {"name": "Crystal Clear (HD)", "rate": rate_adj, "pitch": pitch_adj, "suffix": "hd"},
            {"name": "Fast Radio / Ad", "rate": "+25%", "pitch": "+2Hz", "suffix": "radio"},
            {"name": "Soft / Narrative", "rate": "-15%", "pitch": "-3Hz", "suffix": "soft"}
        ]
        
        tasks, m_res, f_res = [], [], []
        
        for s in styles:
            m_fn = f"m_{base_id}_{s['suffix']}.mp3"
            m_path = os.path.join(AUDIO_DIR, m_fn)
            tasks.append(edge_tts.Communicate(processed_text, group["male"], rate=s['rate'], pitch=s['pitch']).save(m_path))
            m_res.append({"style": s['name'], "url": f"/api/audio/{m_fn}"})

            f_fn = f"f_{base_id}_{s['suffix']}.mp3"
            f_path = os.path.join(AUDIO_DIR, f_fn)
            tasks.append(edge_tts.Communicate(processed_text, group["female"], rate=s['rate'], pitch=s['pitch']).save(f_path))
            f_res.append({"style": s['name'], "url": f"/api/audio/{f_fn}"})
        
        await asyncio.gather(*tasks)
        return {"status": "success", "male_samples": m_res, "female_samples": f_res}
    
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio/{file_name}")
async def get_audio(file_name: str):
    file_path = os.path.join(AUDIO_DIR, file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="Audio file not found")

# For local testing only
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
