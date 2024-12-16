import os
import sys
import signal
import time
import asyncio
import edge_tts
from flask import Flask, request, redirect, jsonify
from google.cloud import storage
from concurrent.futures import ThreadPoolExecutor

now_dir = os.getcwd()
sys.path.append(now_dir)

from core import run_infer_script, run_download_script, import_voice_converter

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=50)  # High concurrency support

@app.route("/download/<path:url>", methods=["GET"])
def download(url):
    file_path = run_download_script(url)
    if file_path == "Model downloaded successfully.":
        if "text/html" in request.headers.get("Accept", ""):
            return redirect("https://applio.org/models/downloaded", code=302)
        else:
            return ""
    else:
        return "Error: Unable to download file", 500

@app.route("/shutdown", methods=["POST"])
def shutdown():
    print("This Flask server is shutting down... Please close the window!")
    os.kill(os.getpid(), signal.SIGTERM)

@app.route("/api/v1/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

async def synthesize_tts(text, voice, rate=0):
    """Synthesize text using edge-tts directly"""
    output_path = os.path.join(now_dir, "assets", "audios", f"tts_output_{int(time.time())}.wav")
    rates = f"+{rate}%" if rate >= 0 else f"{rate}%"
    await edge_tts.Communicate(text, voice, rate=rates).save(output_path)
    return output_path

def run_synthesis(text, voice, rate, **kwargs):
    """Run TTS synthesis and voice conversion in thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tts_output = loop.run_until_complete(synthesize_tts(text, voice, rate))
    loop.close()

    # Run voice conversion if model is specified
    if kwargs.get('pth_path'):
        output_rvc = os.path.join(now_dir, "assets", "audios", f"tts_rvc_output_{int(time.time())}.wav")
        infer_pipeline = import_voice_converter()
        infer_pipeline.convert_audio(
            audio_input_path=tts_output,
            audio_output_path=output_rvc,
            **kwargs
        )
        os.remove(tts_output)  # Clean up intermediate file
        return f"Text synthesized and converted successfully.", output_rvc

    return f"Text synthesized successfully.", tts_output

@app.route("/api/v1/tts", methods=["POST"])
def synthesize_text():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()
    if "text" not in data:
        return jsonify({"error": "Missing text parameter"}), 400

    try:
        # Run synthesis in thread pool
        future = executor.submit(
            run_synthesis,
            text=data["text"],
            voice=data.get("voice", "en-US-JennyNeural"),
            rate=data.get("speed", 0),
            pitch=data.get("pitch", 0),
            filter_radius=data.get("filter_radius", 3),
            index_rate=data.get("index_rate", 0.75),
            volume_envelope=data.get("volume_envelope", 1),
            protect=data.get("protect", 0.5),
            hop_length=data.get("hop_length", 128),
            f0_method=data.get("f0_method", "rmvpe"),
            pth_path=data.get("model_file", ""),
            index_path=data.get("index_file", ""),
            split_audio=data.get("split_audio", False),
            f0_autotune=data.get("autotune", False),
            f0_autotune_strength=data.get("autotune_strength", 1),
            clean_audio=data.get("clean_audio", True),
            clean_strength=data.get("clean_strength", 0.5),
            export_format=data.get("export_format", "WAV"),
            f0_file=None,
            embedder_model=data.get("embedder_model", "contentvec"),
            embedder_model_custom=data.get("embedder_model_custom", None),
            sid=data.get("sid", 0)
        )

        # Get result from future
        output_info, output_path = future.result()

        response_data = {
            "status": "success",
            "message": output_info,
            "local_path": output_path
        }

        # Upload to Google Cloud Storage if configured
        if os.getenv("GCS_BUCKET_NAME"):
            try:
                storage_client = storage.Client()
                bucket = storage_client.bucket(os.getenv("GCS_BUCKET_NAME"))
                blob_name = f"tts_output_{int(time.time())}.{data.get('export_format', 'wav').lower()}"
                blob = bucket.blob(blob_name)
                blob.upload_from_filename(output_path)
                response_data["gcs_path"] = f"gs://{os.getenv('GCS_BUCKET_NAME')}/{blob_name}"
            except Exception as gcs_error:
                response_data["gcs_error"] = str(gcs_error)

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)
