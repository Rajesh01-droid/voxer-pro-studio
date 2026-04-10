from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import edge_tts
import uuid
import os
from pydantic import BaseModel

app = FastAPI()

# CORS allow karna zaroori hai taake frontend connect ho sake
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

AUDIO_DIR = "/tmp"
COUNTER_FILE = "counter.txt"

if not os.path.exists(AUDIO_DIR): 
    os.makedirs(AUDIO_DIR)

# Crystal Clear Models
VOICE_MODELS = {
    "English": {"m": "en-US-AndrewNeural", "f": "en-US-AvaNeural"},
    "Hindi": {"m": "hi-IN-ArunNeural", "f": "hi-IN-SwaraNeural"}
}

def get_count(increment=False):
    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "w") as f: f.write("1250") # Base traffic start
    
    with open(COUNTER_FILE, "r") as f:
        count = int(f.read())
    
    if increment:
        count += 1
        with open(COUNTER_FILE, "w") as f: f.write(str(count))
    return count

class VoiceRequest(BaseModel):
    text: str
    voice_group: str
    gender: str

@app.get("/api/stats")
async def get_stats():
    return {"total_generated": get_count()}

@app.post("/api/generate")
async def generate_voice(request: VoiceRequest):
    try:
        if not request.text.strip(): return {"error": "Empty"}
        
        # Urdu/Hindi detection logic
        lang = "Hindi" if "Hindi" in request.voice_group or "Urdu" in request.voice_group else "English"
        selected_voice = VOICE_MODELS[lang][request.gender]
        
        # Roman Urdu tuning for Crystal Clarity
        rate = "-5%" if lang == "Hindi" else "+0%"
        pitch = "-2Hz" if request.gender == "m" and lang == "Hindi" else "+0Hz"
        
        base_id = uuid.uuid4().hex[:10]
        filename = f"{base_id}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        
        communicate = edge_tts.Communicate(request.text, selected_voice, rate=rate, pitch=pitch)
        await communicate.save(filepath)
        
        new_count = get_count(increment=True)
        
        return {
            "status": "success", 
            "url": f"/api/audio/{filename}?v={base_id}",
            "count": new_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio/{file_name}")
async def get_audio(file_name: str):
    file_path = os.path.join(AUDIO_DIR, file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
