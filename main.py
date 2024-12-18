"""
FastAPI application for TTS and RVC voice conversion.

Endpoints:
- /api/tts: Text-to-Speech synthesis with configurable voice and parameters
- /api/tts-rvc: TTS with Morgan Freeman voice conversion using RVC model

Models:
- TTS: Microsoft Edge TTS (default: en-US-GuyNeural)
- RVC: Morgan Freeman voice model (logs/weights/RVC/Morgan-Freeman.pth)

Configuration:
- RVC Parameters:
  - index_rate: 0.75 (voice similarity)
  - protect: 0.5 (consonant protection)
  - f0_method: rmvpe (pitch extraction)
  - clean_audio: True (audio enhancement)
  - clean_strength: 0.7
  - embedder_model: contentvec

Authentication:
- Requires X-API-Key header with valid API key
"""

from fastapi import FastAPI, Security, Depends, HTTPException, Request
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import JSONResponse
from gradio.routes import mount_gradio_app
import uvicorn
from app import Applio
from core import run_tts_script
import os
import edge_tts
from rvc.infer.infer import VoiceConverter

app = FastAPI(title="Applio API", version="1.0.0")
api_key_header = APIKeyHeader(name="X-API-Key")

async def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key != os.environ.get("APPLIO_API_WRITE"):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    return api_key

from pydantic import BaseModel

class TTSRequest(BaseModel):
    text: str
    voice: str
    rate: int = 0
    pitch: int = 0
    filter_radius: int = 3
    index_rate: float = 0.75
    protect: float = 0.33
    export_format: str = "wav"

class RVCTTSRequest(BaseModel):
    text: str
    voice: str = "en-US-GuyNeural"

@app.post("/api/tts", dependencies=[Security(get_api_key)])
async def tts_endpoint(request: TTSRequest):
    try:
        output_tts_path = os.path.join("assets", "tts", f"tts_{request.text[:10]}_{request.voice}.wav")
        output_rvc_path = os.path.join("assets", "tts", f"rvc_{request.text[:10]}_{request.voice}.{request.export_format}")

        message, output_path = run_tts_script(
            tts_file="",
            tts_text=request.text,
            tts_voice=request.voice,
            tts_rate=request.rate,
            pitch=request.pitch,
            filter_radius=request.filter_radius,
            index_rate=request.index_rate,
            volume_envelope=1,
            protect=request.protect,
            hop_length=128,
            f0_method="rmvpe",
            output_tts_path=output_tts_path,
            output_rvc_path=output_rvc_path,
            pth_path="",  # Will use default from config
            index_path="",  # Will use default from config
            split_audio=False,
            f0_autotune=False,
            f0_autotune_strength=0.0,
            clean_audio=False,
            clean_strength=0.0,
            export_format=request.export_format,
            f0_file="",
            embedder_model="hubert_base",
            sid=0
        )

        return JSONResponse({
            "status": "success",
            "message": message,
            "audio_path": output_path
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.post("/api/tts-rvc", dependencies=[Security(get_api_key)])
async def tts_rvc_endpoint(request: RVCTTSRequest):
    try:
        # Generate TTS audio with Guy Neural voice
        tts = edge_tts.Communicate(text=request.text, voice=request.voice)
        audio_path = os.path.join("assets", "tts", "rvc_tts.wav")
        await tts.save(audio_path)

        # Initialize voice converter
        converter = VoiceConverter()

        # RVC conversion parameters
        rvc_params = {
            "audio_input_path": audio_path,
            "audio_output_path": os.path.join("assets", "tts", "rvc_output.wav"),
            "model_path": os.path.join("logs", "weights", "RVC", "Morgan-Freeman.pth"),
            "index_path": os.path.join("logs", "weights", "RVC", "added_IVF455_Flat_nprobe_1_Morgan-Freeman_v2.index"),
            "index_rate": 0.75,  # Default for good voice similarity
            "protect": 0.5,      # Protect voiceless consonants
            "f0_method": "rmvpe",
            "embedder_model": "contentvec",
            "clean_audio": True,
            "clean_strength": 0.7,
            "export_format": "WAV"
        }

        # Perform voice conversion
        converter.convert_audio(**rvc_params)

        return JSONResponse({
            "status": "success",
            "message": f"Text '{request.text}' synthesized successfully with Morgan Freeman's voice.",
            "audio_path": rvc_params["audio_output_path"]
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# Mount Gradio app
app = mount_gradio_app(app, Applio, path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)