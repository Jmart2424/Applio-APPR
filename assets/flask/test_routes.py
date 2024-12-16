import os
import sys
import time
import asyncio
import edge_tts
import requests
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from google.cloud import storage
from datetime import datetime

now_dir = os.getcwd()
sys.path.append(now_dir)

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=50)  # High concurrency support
storage_client = storage.Client()
bucket_name = os.getenv('GCS_BUCKET_NAME', 'applio-tts-output')

try:
    bucket = storage_client.get_bucket(bucket_name)
except Exception:
    bucket = storage_client.create_bucket(bucket_name)

@app.route("/api/v1/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

async def synthesize_tts(text, voice, rate=0):
    """Synthesize text using edge-tts directly"""
    timestamp = int(time.time())
    date_prefix = datetime.now().strftime('%Y/%m/%d')
    filename = f"tts_output_{timestamp}.wav"
    output_path = os.path.join(now_dir, "assets", "audios", filename)
    gcs_path = f"{date_prefix}/{filename}"

    rates = f"+{rate}%" if rate >= 0 else f"{rate}%"
    start_time = time.time()
    await edge_tts.Communicate(text, voice, rate=rates).save(output_path)
    synthesis_time = time.time() - start_time

    # Upload to GCS
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(output_path)
    blob.make_public()

    print(f"Synthesis completed in {synthesis_time:.2f} seconds")
    return output_path, synthesis_time, blob.public_url

def run_synthesis(text, voice, rate=0):
    """Run TTS synthesis in thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    output_path, synthesis_time, public_url = loop.run_until_complete(synthesize_tts(text, voice, rate))
    loop.close()
    return output_path, synthesis_time, public_url

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
            rate=data.get("speed", 0)
        )

        # Get result from future
        output_path, synthesis_time, public_url = future.result()

        # Handle webhook callback if provided
        callback_url = data.get("callback_url")
        if callback_url:
            executor.submit(
                requests.post,
                callback_url,
                json={
                    "status": "success",
                    "audio_url": public_url,
                    "synthesis_time": synthesis_time
                }
            )

        return jsonify({
            "status": "success",
            "message": "Text synthesized successfully",
            "local_path": output_path,
            "public_url": public_url,
            "synthesis_time": synthesis_time
        })

    except Exception as e:
        error_response = {"error": str(e)}
        if data.get("callback_url"):
            executor.submit(
                requests.post,
                data["callback_url"],
                json={"status": "error", "error": str(e)}
            )
        return jsonify(error_response), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)
