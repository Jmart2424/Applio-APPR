import os
import sys
import signal
import time
from flask import Flask, request, redirect, jsonify
from google.cloud import storage
from concurrent.futures import ThreadPoolExecutor

now_dir = os.getcwd()
sys.path.append(now_dir)

from core import run_tts_script, run_download_script

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

@app.route("/api/v1/tts", methods=["POST"])
def synthesize_text():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()
    if "text" not in data:
        return jsonify({"error": "Missing text parameter"}), 400

    try:
        # Run TTS synthesis in thread pool
        future = executor.submit(
            run_tts_script,
            tts_file="",  # Empty for direct text input
            tts_text=data["text"],
            tts_voice=data.get("voice", "en-US-JennyNeural"),
            tts_rate=data.get("speed", 0),
            pitch=data.get("pitch", 0),
            filter_radius=data.get("filter_radius", 3),
            index_rate=data.get("index_rate", 0.75),
            volume_envelope=data.get("volume_envelope", 1),
            protect=data.get("protect", 0.5),
            hop_length=data.get("hop_length", 128),
            f0_method=data.get("f0_method", "rmvpe"),
            output_tts_path=os.path.join(now_dir, "assets", "audios", f"tts_output_{int(time.time())}.wav"),
            output_rvc_path=os.path.join(now_dir, "assets", "audios", f"tts_rvc_output_{int(time.time())}.wav"),
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

        # Upload to Google Cloud Storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(os.getenv("GCS_BUCKET_NAME"))
        blob_name = f"tts_output_{int(time.time())}.{data.get('export_format', 'wav').lower()}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(output_path)

        return jsonify({
            "status": "success",
            "message": output_info,
            "gcs_path": f"gs://{os.getenv('GCS_BUCKET_NAME')}/{blob_name}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="localhost", port=8000, threaded=True)
