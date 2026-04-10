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
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

# Crystal Clear Desi & English Models
# 'hi-IN-ArunNeural' male voice ke liye bohot behtar hai Roman Urdu ke liye
VOICE_MODELS = {
    "English": {"m": "en-US-AndrewNeural", "f": "en-US-AvaNeural"},
    "Hindi": {"m": "hi-IN-ArunNeural", "f": "hi-IN-SwaraNeural"}
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
        
        # Language Logic fix
        lang = "Hindi" if "Hindi" in request.voice_group or "Urdu" in request.voice_group else "English"
        
        # Voice selection
        selected_voice = VOICE_MODELS[lang].get(request.gender, VOICE_MODELS[lang]["m"])
        
        # TUNING FOR CRYSTAL CLARITY:
        # Roman Urdu ko clear karne ke liye thori base aur slow speed zaroori hai
        if lang == "Hindi":
            rate = "-5%"  # Thora slow taake words clear samajh aayein
            pitch = "-2Hz" if request.gender == "m" else "+0Hz" # Male voice ko deep aur professional banane ke liye
        else:
            rate = "+0%"
            pitch = "+0Hz"
        
        base_id = uuid.uuid4().hex[:10]
        filename = f"{base_id}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        
        # Edge TTS Communication
        communicate = edge_tts.Communicate(request.text, selected_voice, rate=rate, pitch=pitch)
        await communicate.save(filepath)
        
        # File check logic
        if os.path.exists(filepath):
            return {"status": "success", "url": f"/api/audio/{filename}?v={base_id}"}
        else:
            raise Exception("File generation failed")

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio/{file_name}")
async def get_audio(file_name: str):
    file_path = os.path.join(AUDIO_DIR, file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
