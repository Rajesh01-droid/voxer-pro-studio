import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import edge_tts
import uuid
import os
import re
import asyncio
from pydantic import BaseModel
# Mangum ki zaroorat par sakti hai agar direct FastAPI na chale
# from mangum import Mangum 

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Vercel par sirf /tmp folder mein file save ho sakti hai temporary
AUDIO_DIR = "/tmp/generated_audio"
if not os.path.exists(AUDIO_DIR): 
    os.makedirs(AUDIO_DIR)

class VoiceRequest(BaseModel):
    text: str
    voice_group: str

# ... (Aapka emotion detection aur clean_text wala function yahan rahega) ...

@app.post("/generate")
async def generate_voice(request: VoiceRequest):
    if not request.text.strip(): raise HTTPException(status_code=400, detail="Text required")
    
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
            m_res.append({"style": s['name'], "url": f"/api/audio/{m_fn}"}) # Path changed

            f_fn = f"f_{base_id}_{s['suffix']}.mp3"
            f_path = os.path.join(AUDIO_DIR, f_fn)
            tasks.append(edge_tts.Communicate(processed_text, group["female"], rate=s['rate'], pitch=s['pitch']).save(f_path))
            f_res.append({"style": s['name'], "url": f"/api/audio/{f_fn}"}) # Path changed
        
        await asyncio.gather(*tasks)
        return {"status": "success", "male_samples": m_res, "female_samples": f_res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Audio files server karne ke liye endpoint
@app.get("/api/audio/{file_name}")
async def get_audio(file_name: str):
    file_path = os.path.join(AUDIO_DIR, file_name)
    if os.path.exists(file_path):
        from fastapi.responses import FileResponse
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

# Frontend mounting Vercel ke liye nikal dein kyunki vercel.json handle karega
# app.mount("/", StaticFiles(directory=".", html=True), name="frontend")

# Vercel ko is 'app' object ki zaroorat hoti hai