from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import edge_tts
import uuid
import os
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

AUDIO_DIR = "/tmp"
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

# Crystal Clear Desi & English Models
VOICE_MODELS = {
    "English": {"m": "en-US-AndrewNeural", "f": "en-US-AvaNeural"},
    "Hindi": {"m": "hi-IN-MadhurNeural", "f": "hi-IN-SwaraNeural"} 
}
# Note: Madhur ya Arun dono ache hain, Madhur thora zyada natural hai Roman Urdu ke liye.

class VoiceRequest(BaseModel):
    text: str
    voice_group: str
    gender: str

@app.post("/api/generate")
async def generate_voice(request: VoiceRequest):
    try:
        if not request.text.strip(): 
            return {"error": "Text is empty"}
        
        # --- FIXING LANGUAGE LOGIC ---
        # Hum check kar rahe hain ke agar text Hindi/Urdu context mein hai
        v_group = request.voice_group.lower()
        if "hindi" in v_group or "urdu" in v_group:
            lang = "Hindi"
        else:
            lang = "English"
        
        # --- FIXING VOICE SELECTION ---
        # Gender 'm' or 'f' check kar rahe hain
        gender = request.gender.lower()
        if gender not in ["m", "f"]:
            gender = "m" # Default male
            
        selected_voice = VOICE_MODELS[lang][gender]
        
        # TUNING FOR CRYSTAL CLARITY
        if lang == "Hindi":
            # Roman Urdu ke liye thora slow aur deep pitch best rehti hai
            rate = "-5%"
            pitch = "-1Hz" if gender == "m" else "+0Hz"
        else:
            rate = "+0%"
            pitch = "+0Hz"
        
        base_id = uuid.uuid4().hex[:10]
        filename = f"{base_id}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        
        # Edge TTS Communication
        communicate = edge_tts.Communicate(request.text, selected_voice, rate=rate, pitch=pitch)
        await communicate.save(filepath)
        
        if os.path.exists(filepath):
            return {"status": "success", "url": f"/api/audio/{filename}?v={base_id}"}
        else:
            raise Exception("File generation failed")

    except Exception as e:
        print(f"Error occurred: {str(e)}")
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
