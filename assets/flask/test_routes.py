import os
import sys
import time
import asyncio
import edge_tts
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor

now_dir = os.getcwd()
sys.path.append(now_dir)

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=50)  # High concurrency support

@app.route("/api/v1/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

async def synthesize_tts(text, voice, rate=0):
    """Synthesize text using edge-tts directly"""
    output_path = os.path.join(now_dir, "assets", "audios", f"tts_output_{int(time.time())}.wav")
    rates = f"+{rate}%" if rate >= 0 else f"{rate}%"
    start_time = time.time()
    await edge_tts.Communicate(text, voice, rate=rates).save(output_path)
    synthesis_time = time.time() - start_time
    print(f"Synthesis completed in {synthesis_time:.2f} seconds")
    return output_path, synthesis_time

def run_synthesis(text, voice, rate=0):
    """Run TTS synthesis in thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    output_path, synthesis_time = loop.run_until_complete(synthesize_tts(text, voice, rate))
    loop.close()
    return output_path, synthesis_time

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
        output_path, synthesis_time = future.result()

        return jsonify({
            "status": "success",
            "message": "Text synthesized successfully",
            "local_path": output_path,
            "synthesis_time": synthesis_time
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)
