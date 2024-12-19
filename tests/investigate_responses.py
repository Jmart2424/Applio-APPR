"""
Investigation of FastAPI response types for audio file handling.
"""
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Dict
import os

def investigate_file_response():
    """Investigate FileResponse capabilities for audio files."""
    print("=== FileResponse Investigation ===")
    print("\nKey Features:")
    print("- Media type handling:", FileResponse.media_type)
    print("- Supports chunked transfer:", hasattr(FileResponse, 'chunk_size'))
    print("- Headers:", FileResponse.headers.__annotations__)
    
    # Example usage for WAV file
    example = FileResponse(
        path="assets/tts/rvc_output.wav",
        media_type="audio/wav",
        filename="output.wav"
    )
    print("\nExample WAV response headers:", example.headers)

def investigate_streaming_response():
    """Investigate StreamingResponse capabilities."""
    print("\n=== StreamingResponse Investigation ===")
    print("\nKey Features:")
    print("- Supports async streaming:", StreamingResponse.__doc__)
    print("- Headers:", StreamingResponse.headers.__annotations__)
    
    # Example generator for streaming audio
    async def audio_generator():
        chunk_size = 1024 * 8
        with open("assets/tts/rvc_output.wav", "rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk
    
    example = StreamingResponse(
        audio_generator(),
        media_type="audio/wav"
    )
    print("\nExample streaming headers:", example.headers)

if __name__ == "__main__":
    investigate_file_response()
    investigate_streaming_response()
